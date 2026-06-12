"""Parking <-> rental proximity matching (rebuilt after each scrape cycle)."""
import logging
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.cities import CityConfig
from app.core.config import settings
from app.db.models import GeoPrecision, Listing, ParkingMatch, ParkingSpot, utcnow
from app.services.geo import haversine_m, walk_minutes

log = logging.getLogger(__name__)

_APPROX = {GeoPrecision.ZONE.value, GeoPrecision.CITY.value, GeoPrecision.NONE.value}


def _chunks(seq: list, n: int = 500):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def rebuild_matches(db: Session, city: CityConfig) -> int:
    cutoff = utcnow() - timedelta(days=settings.listing_active_days)
    listings = db.scalars(
        select(Listing).where(
            Listing.city_slug == city.slug,
            Listing.last_seen_at >= cutoff,
            Listing.lat.is_not(None),
        )
    ).all()
    spots = db.scalars(
        select(ParkingSpot).where(
            ParkingSpot.city_slug == city.slug,
            ParkingSpot.last_seen_at >= cutoff,
            ParkingSpot.lat.is_not(None),
        )
    ).all()

    ids = [listing.id for listing in listings]
    for chunk in _chunks(ids):  # SQLite parameter limit safety
        db.execute(delete(ParkingMatch).where(ParkingMatch.listing_id.in_(chunk)))

    n = 0
    for listing in listings:
        cands: list[tuple[float, ParkingSpot]] = []
        for spot in spots:
            d = haversine_m(listing.lat, listing.lon, spot.lat, spot.lon)
            if d <= settings.parking_match_max_m:
                cands.append((d, spot))
        cands.sort(key=lambda x: x[0])
        for d, spot in cands[: settings.parking_matches_per_listing]:
            db.add(
                ParkingMatch(
                    listing_id=listing.id,
                    parking_id=spot.id,
                    distance_m=int(d),
                    walk_min=walk_minutes(d),
                    is_approx=(
                        listing.geo_precision in _APPROX or spot.geo_precision in _APPROX
                    ),
                )
            )
            n += 1
    db.commit()
    log.info(
        "matching %s: %d listings x %d spots -> %d matches",
        city.slug, len(listings), len(spots), n,
    )
    return n
