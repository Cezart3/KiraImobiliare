"""RawListing -> extraction -> geolocation -> DB upsert."""
import hashlib
import logging
import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cities import (
    CityConfig,
    Place,
    find_landmark,
    find_town,
    find_zone,
    mentions_other_city,
)
from app.core.config import settings
from app.core.textutil import fold, redact_personal
from app.db.models import GeoPrecision, Listing, ParkingSpot, utcnow
from app.scraping.base import RawListing
from app.scraping.extractors.address import extract_street, has_house_number
from app.scraping.extractors.heating import classify_heating
from app.scraping.extractors.parking import (
    APARTMENT_WORDS,
    classify_parking,
    classify_parking_spot,
    looks_like_parking_only,
)
from app.scraping.extractors.price import to_eur
from app.scraping.extractors.rooms import extract_floor, extract_rooms, extract_surface
from app.services.geo import Geocoder, haversine_m

log = logging.getLogger(__name__)

_SHORT_STAY = re.compile(
    r"regim hotelier|pe noapte|/\s*noapte|/\s*zi\b|pe zi\b|nightly|"
    r"cazare (?:muncitori|in regim)|zilnic\b|saptamanal|pe termen scurt"
)

# \b keeps "nenegociabil" (fixed price) from matching
_NEGOTIABLE = re.compile(r"\bnegocia")

# sale ads leaking into rental feeds ("De vânzare apartament...", 126.000 EUR)
_SALE_AD = re.compile(r"\bde vanzare\b|\bvand\b|\bvindem\b")

_PRECISION_RANK = {
    "exact": 5, "street": 4, "landmark": 3, "zone": 2, "city": 1, "none": 0
}


def _full_text(raw: RawListing) -> str:
    return " ".join(p for p in (raw.title, raw.description, raw.extra_text, raw.location_text) if p)


def _naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def drop_reason_rent(raw: RawListing, price_eur: float | None) -> str | None:
    if looks_like_parking_only(raw.title):
        return "parking-only"
    if _SALE_AD.search(fold(raw.title)):
        return "sale-ad"
    if _SHORT_STAY.search(fold(_full_text(raw))):
        return "short-stay"
    if price_eur is not None and price_eur < settings.rent_min_eur:
        return "below-min-price"
    if price_eur is not None and price_eur > settings.rent_max_eur:
        return "sale-or-misparse"
    return None


def _geolocate(
    city: CityConfig,
    zone: Place | None,
    town: Place | None,
    street: str,
    landmark: Place | None,
    geocoder: Geocoder,
) -> tuple[float, float, str]:
    """Best coordinates we can justify, in order of specificity:
    street(+number) > known landmark > zone centroid > city centre.
    Town listings use the town centroid (streets there would mis-geocode under
    the main city's viewbox)."""
    if town:
        return town.lat, town.lon, GeoPrecision.ZONE.value
    if street:
        hint = f"{street}, {zone.name}" if zone else street
        coords = geocoder.geocode(hint, city)
        max_m = city.radius_km * 1800
        if coords and haversine_m(coords[0], coords[1], city.lat, city.lon) <= max_m:
            prec = GeoPrecision.EXACT if has_house_number(street) else GeoPrecision.STREET
            return coords[0], coords[1], prec.value
    if landmark:
        # exact coordinates of a known reference point — no network call needed
        return landmark.lat, landmark.lon, GeoPrecision.LANDMARK.value
    if zone:
        return zone.lat, zone.lon, GeoPrecision.ZONE.value
    return city.lat, city.lon, GeoPrecision.CITY.value


def apply_extractions(
    listing: Listing, raw: RawListing, city: CityConfig, geocoder: Geocoder
) -> None:
    """Idempotent: runs on insert, on re-scrape, and after detail enrichment."""
    text = _full_text(raw)

    # store redacted copies (no phone numbers / emails — GDPR data minimisation);
    # extraction below still uses the in-memory `text` which keeps street/landmark
    if raw.title:
        listing.title = redact_personal(raw.title)
    if raw.description and len(raw.description) > len(listing.description or ""):
        listing.description = redact_personal(raw.description)
    if raw.images:
        listing.images = raw.images[:8]
    if raw.location_text:
        listing.location_raw = raw.location_text[:255]
    if raw.source_id:
        listing.source_id = raw.source_id

    price = to_eur(raw.price_value, raw.price_currency, settings.ron_per_eur)
    if price is not None and price > settings.rent_max_eur:
        price = None  # parse glitch — keep the listing, not the rocket price
    if price is not None:
        listing.price_eur = price
        listing.price_raw = f"{raw.price_value} {raw.price_currency}".strip()[:64]
    # sticky: detail text often carries it while the re-scraped card does not
    if _NEGOTIABLE.search(fold(text)):
        listing.price_negotiable = True

    listing.rooms = raw.rooms or extract_rooms(text) or listing.rooms
    listing.surface_m2 = raw.surface_m2 or extract_surface(text) or listing.surface_m2
    listing.floor = raw.floor or extract_floor(text) or listing.floor

    status, conf = classify_parking(text, raw.parking_hint)
    if conf >= (listing.parking_confidence or 0) or listing.parking_status in (None, "unknown"):
        listing.parking_status = status.value
        listing.parking_confidence = conf

    heating = classify_heating(text)
    if heating.value != "unknown" or not listing.heating:
        listing.heating = heating.value

    town = find_town(city, raw.location_text, raw.title)
    zone = find_zone(city, raw.location_text, raw.title, (raw.description or "")[:220])
    listing.in_nearby_town = town is not None
    listing.town_slug = town.slug if town else None
    if zone:
        listing.zone_slug = zone.slug

    street = extract_street(text, city.stop_terms())
    # a known reference point (mall, OMV, Expo...) named in title/desc — better
    # than the zone centroid when there's no explicit street
    landmark = find_landmark(city, raw.title, raw.location_text, raw.description)
    listing.address_extracted = (
        f"{street}, {zone.name}" if street and zone
        else street
        or (f"lângă {landmark.name}" if landmark else "")
        or (zone.name if zone else "")
        or (town.name if town else "")
    )[:255]

    new_rank = (
        5 if (street and has_house_number(street))
        else 4 if street
        else 3 if landmark
        else 2 if (zone or town)
        else 1
    )
    if new_rank > _PRECISION_RANK.get(listing.geo_precision or "none", 0):
        lat, lon, prec = _geolocate(city, zone, town, street, landmark, geocoder)
        listing.lat, listing.lon, listing.geo_precision = lat, lon, prec

    if listing.price_eur and listing.rooms and listing.surface_m2:
        key = (
            f"{city.slug}|{listing.rooms}|{round(listing.surface_m2)}|"
            f"{round(listing.price_eur / 10) * 10}"
        )
        listing.dedup_group = hashlib.sha1(key.encode()).hexdigest()[:16]


def upsert_rental(
    db: Session, raw: RawListing, city: CityConfig, geocoder: Geocoder
) -> tuple[Listing | None, bool, str | None]:
    """Returns (listing, created, drop_reason)."""
    price = to_eur(raw.price_value, raw.price_currency, settings.ron_per_eur)
    reason = drop_reason_rent(raw, price)
    if reason:
        return None, False, reason
    if mentions_other_city(raw.location_text, city.slug) and not find_town(
        city, raw.location_text
    ):
        return None, False, "other-city"

    existing = db.scalar(select(Listing).where(Listing.url == raw.url))
    created = existing is None
    listing = existing or Listing(site=raw.site, url=raw.url, city_slug=city.slug)
    if created:
        db.add(listing)

    apply_extractions(listing, raw, city, geocoder)
    if raw.posted_at:
        listing.posted_at = _naive_utc(raw.posted_at)
    listing.last_seen_at = utcnow()
    db.flush()
    return listing, created, None


def upsert_parking(
    db: Session,
    raw: RawListing,
    city: CityConfig,
    geocoder: Geocoder,
    category_trusted: bool = False,
) -> tuple[ParkingSpot | None, bool, str | None]:
    """Standalone parking/garage rentals. category_trusted=True for dedicated
    garage categories (storia /garaj); otherwise the title must look parking-only."""
    ft_title = fold(raw.title)
    if APARTMENT_WORDS.search(ft_title):
        return None, False, "apartment-leak"
    if not category_trusted and not looks_like_parking_only(raw.title):
        return None, False, "not-parking"
    price = to_eur(raw.price_value, raw.price_currency, settings.ron_per_eur)
    if price is not None and price > settings.parking_max_eur:
        return None, False, "too-expensive"
    if mentions_other_city(raw.location_text, city.slug) and not find_town(
        city, raw.location_text
    ):
        return None, False, "other-city"

    existing = db.scalar(select(ParkingSpot).where(ParkingSpot.url == raw.url))
    created = existing is None
    spot = existing or ParkingSpot(site=raw.site, url=raw.url, city_slug=city.slug)
    if created:
        db.add(spot)

    text = _full_text(raw)
    spot.title = redact_personal(raw.title) or spot.title
    if raw.description and len(raw.description) > len(spot.description or ""):
        spot.description = redact_personal(raw.description)
    if price is not None:
        spot.price_eur = price
    kind, numbered = classify_parking_spot(text)
    spot.kind = kind.value
    spot.is_numbered = numbered

    town = find_town(city, raw.location_text, raw.title)
    zone = find_zone(city, raw.location_text, raw.title, (raw.description or "")[:220])
    if zone:
        spot.zone_slug = zone.slug
    street = extract_street(text, city.stop_terms())
    spot.address_extracted = (
        f"{street}, {zone.name}" if street and zone
        else street or (zone.name if zone else "") or (town.name if town else "")
    )[:255]

    new_rank = (
        4 if (street and has_house_number(street))
        else 3 if street
        else 2 if (zone or town)
        else 1
    )
    if new_rank > _PRECISION_RANK.get(spot.geo_precision or "none", 0):
        lat, lon, prec = _geolocate(city, zone, town, street, None, geocoder)
        spot.lat, spot.lon, spot.geo_precision = lat, lon, prec

    spot.last_seen_at = utcnow()
    db.flush()
    return spot, created, None
