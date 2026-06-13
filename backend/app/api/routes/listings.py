import math
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.core.cities import load_cities
from app.core.config import settings
from app.db.models import Listing, ParkingMatch, utcnow
from app.schemas.listing import (
    ListingDetailOut,
    ListingOut,
    ListingPage,
    ParkingMatchOut,
    ParkingSpotOut,
)
from app.services.geo import Geocoder, haversine_m, maps_walk_link, walk_minutes

router = APIRouter(tags=["listings"])

_STATUS_FILTERS = {"included", "likely_included", "area_possible", "none", "unknown"}
_MAX_ORIGINS = 3  # cap geocoding work per request


def _resolve_origins(
    db: Session, near: list[str], city_slug: str
) -> list[tuple[float, float, str]]:
    """Geocode up to a few user-supplied origin addresses (free, cached). Returns
    (lat, lon, label) for each one we could place.

    Hardened against abuse: caps the number of origins, the address length, and
    the live-geocode budget per request (cached lookups are unlimited and free;
    only genuinely-new addresses hit Nominatim, max 1/sec per OSM policy)."""
    cities = load_cities()
    city = cities.get(city_slug)
    if city is None:
        return []
    # small per-request budget: a normal user supplies 1-3 distinct addresses;
    # this stops someone spamming unique strings from hammering OSM through us
    geocoder = Geocoder(db, budget=_MAX_ORIGINS)
    out: list[tuple[float, float, str]] = []
    seen: set[str] = set()
    for raw in near[:_MAX_ORIGINS]:
        label = " ".join((raw or "").split()).strip()[:120]  # cap length
        if not label or label.lower() in seen:
            continue
        seen.add(label.lower())
        coords = geocoder.geocode(label, city)
        if coords:
            out.append((coords[0], coords[1], label))
    db.commit()  # persist any new GeoCache rows
    return out


def _distances(
    rows: list[Listing], origins: list[tuple[float, float, str]]
) -> dict[int, tuple[float, float, float, str]]:
    """For each listing, the distance to the NEAREST origin.
    Returns id -> (meters, origin_lat, origin_lon, origin_label)."""
    result: dict[int, tuple[float, float, float, str]] = {}
    for r in rows:
        if not r.lat or not r.lon:
            continue
        best: tuple[float, float, float, str] | None = None
        for olat, olon, label in origins:
            d = haversine_m(r.lat, r.lon, olat, olon)
            if best is None or d < best[0]:
                best = (d, olat, olon, label)
        if best is not None:
            result[r.id] = best
    return result


def _apply_sql_sort_in_python(rows: list[Listing], sort: str) -> list[Listing]:
    """Same ordering as the SQL path, for when we already have rows in memory."""
    if sort == "price_asc":
        return sorted(rows, key=lambda r: (r.price_eur is None, r.price_eur or 0.0))
    if sort == "price_desc":
        return sorted(rows, key=lambda r: (r.price_eur or 0.0), reverse=True)
    if sort == "parking":
        return sorted(
            rows,
            key=lambda r: (-(r.parking_confidence or 0), r.price_eur or float("inf")),
        )
    # newest
    return sorted(
        rows, key=lambda r: (r.posted_at or r.first_seen_at), reverse=True
    )


def _match_out(listing: Listing, m: ParkingMatch) -> ParkingMatchOut:
    return ParkingMatchOut(
        parking=ParkingSpotOut.model_validate(m.parking),
        distance_m=m.distance_m,
        walk_min=m.walk_min,
        is_approx=m.is_approx,
        maps_url=maps_walk_link(listing.lat, listing.lon, m.parking.lat, m.parking.lon)
        if listing.lat and m.parking.lat
        else "",
    )


@router.get("/listings", response_model=ListingPage)
def list_listings(
    city: str,
    db: Annotated[Session, Depends(get_db)],
    price_min: float | None = None,
    price_max: float | None = None,
    rooms: Annotated[list[int] | None, Query()] = None,
    zones: Annotated[list[str] | None, Query()] = None,
    heating: Annotated[list[str] | None, Query()] = None,
    parking: Annotated[list[str] | None, Query()] = None,
    sites: Annotated[list[str] | None, Query()] = None,
    q: str | None = None,
    include_nearby: bool = False,
    near: Annotated[list[str] | None, Query()] = None,
    sort: Annotated[
        str, Query(pattern="^(newest|price_asc|price_desc|parking|distance)$")
    ] = "newest",
    page: Annotated[int, Query(ge=1, le=1000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=60)] = 24,
):
    cutoff = utcnow() - timedelta(days=settings.listing_active_days)
    conds = [Listing.city_slug == city, Listing.last_seen_at >= cutoff]

    if not include_nearby:
        conds.append(Listing.in_nearby_town.is_(False))
    if price_min is not None:
        conds.append(Listing.price_eur >= price_min)
    if price_max is not None:
        conds.append(Listing.price_eur <= price_max)
    if rooms:
        wanted = set(rooms)
        if 4 in wanted:  # UI sends 4 meaning "4+"
            wanted |= {5, 6}
        conds.append(Listing.rooms.in_(sorted(wanted)))
    if zones:
        zone_cond = Listing.zone_slug.in_(zones)
        if include_nearby:
            # zone chips refer to city zones; nearby towns stay visible alongside
            zone_cond = or_(zone_cond, Listing.in_nearby_town.is_(True))
        conds.append(zone_cond)
    if heating:
        conds.append(Listing.heating.in_(heating))
    if sites:
        conds.append(Listing.site.in_(sites))
    if q:
        like = f"%{q.strip()}%"
        conds.append(or_(Listing.title.ilike(like), Listing.description.ilike(like)))
    if parking:
        pset = set(parking)
        sub = []
        statuses = pset & _STATUS_FILTERS
        if statuses:
            sub.append(Listing.parking_status.in_(statuses))
        if "rentable_nearby" in pset:
            sub.append(Listing.parking_matches.any())
        if sub:
            conds.append(or_(*sub))

    base = select(Listing).where(*conds)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0

    # optional: distances from user-supplied origin address(es). Pure local math
    # on coordinates we already store; geocoding the origins uses Nominatim (free,
    # cached, budget-capped) — no paid API, no per-request cost.
    origins = _resolve_origins(db, near, city) if near else []

    if origins or sort == "distance":
        # distance needs every matching row in memory to sort globally, then slice
        all_rows = db.scalars(base).all()
        dist_by_id = _distances(all_rows, origins) if origins else {}
        if sort == "distance" and origins:
            all_rows.sort(key=lambda r: dist_by_id.get(r.id, (float("inf"),))[0])
        else:
            all_rows = _apply_sql_sort_in_python(all_rows, sort)
        rows = all_rows[(page - 1) * page_size : (page - 1) * page_size + page_size]
    else:
        order = {
            "newest": (func.coalesce(Listing.posted_at, Listing.first_seen_at).desc(),),
            "price_asc": (Listing.price_eur.asc().nulls_last(),),
            "price_desc": (Listing.price_eur.desc().nulls_last(),),
            "parking": (
                Listing.parking_confidence.desc(),
                Listing.price_eur.asc().nulls_last(),
            ),
        }[sort]
        rows = db.scalars(
            base.order_by(*order).offset((page - 1) * page_size).limit(page_size)
        ).all()
        dist_by_id = {}

    matches_by_listing: dict[int, list[ParkingMatch]] = {}
    ids = [r.id for r in rows]
    if ids:
        ms = db.scalars(
            select(ParkingMatch)
            .options(joinedload(ParkingMatch.parking))
            .where(ParkingMatch.listing_id.in_(ids))
            .order_by(ParkingMatch.distance_m)
        ).all()
        for m in ms:
            matches_by_listing.setdefault(m.listing_id, []).append(m)

    items: list[ListingOut] = []
    for r in rows:
        out = ListingOut.model_validate(r)
        out.snippet = (r.description or "")[:220]
        lm = matches_by_listing.get(r.id, [])
        out.parking_match_count = len(lm)
        if lm:
            out.best_parking = _match_out(r, lm[0])
        dist = dist_by_id.get(r.id)
        if dist is not None and r.lat and r.lon:
            meters, olat, olon, label = dist
            out.distance_to_origin_m = int(meters)
            out.distance_to_origin_walk_min = walk_minutes(meters)
            out.distance_origin_label = label
            # free: just a deep-link to Google Maps (opens on the user's device),
            # transit mode so they can see bus options + times there themselves
            out.distance_maps_url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&origin={r.lat},{r.lon}&destination={olat},{olon}&travelmode=transit"
            )
        items.append(out)

    return ListingPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/listings-by-ids", response_model=list[ListingOut])
def listings_by_ids(
    db: Annotated[Session, Depends(get_db)],
    ids: Annotated[list[int], Query()] = [],  # noqa: B006 (FastAPI query default)
    near: Annotated[list[str] | None, Query()] = None,
):
    """Fetch specific listings by id (used by the Favorites view so saved
    listings show regardless of what's currently cached client-side). Honors
    `near` for distance annotation/sorting, like the main list endpoint."""
    if not ids:
        return []
    rows = db.scalars(select(Listing).where(Listing.id.in_(ids[:200]))).all()
    by_id = {r.id: r for r in rows}
    # preserve the caller's id order by default
    ordered = [by_id[i] for i in ids if i in by_id]

    city_slug = ordered[0].city_slug if ordered else None
    origins = _resolve_origins(db, near, city_slug) if (near and city_slug) else []
    dist_by_id = _distances(ordered, origins) if origins else {}
    if origins:
        ordered.sort(key=lambda r: dist_by_id.get(r.id, (float("inf"),))[0])

    match_ids = [r.id for r in ordered]
    matches_by_listing: dict[int, list[ParkingMatch]] = {}
    if match_ids:
        ms = db.scalars(
            select(ParkingMatch)
            .options(joinedload(ParkingMatch.parking))
            .where(ParkingMatch.listing_id.in_(match_ids))
            .order_by(ParkingMatch.distance_m)
        ).all()
        for m in ms:
            matches_by_listing.setdefault(m.listing_id, []).append(m)

    out_list: list[ListingOut] = []
    for r in ordered:
        out = ListingOut.model_validate(r)
        out.snippet = (r.description or "")[:220]
        lm = matches_by_listing.get(r.id, [])
        out.parking_match_count = len(lm)
        if lm:
            out.best_parking = _match_out(r, lm[0])
        dist = dist_by_id.get(r.id)
        if dist is not None and r.lat and r.lon:
            meters, olat, olon, label = dist
            out.distance_to_origin_m = int(meters)
            out.distance_to_origin_walk_min = walk_minutes(meters)
            out.distance_origin_label = label
            out.distance_maps_url = (
                "https://www.google.com/maps/dir/?api=1"
                f"&origin={r.lat},{r.lon}&destination={olat},{olon}&travelmode=transit"
            )
        out_list.append(out)
    return out_list


@router.get("/listings/{listing_id}", response_model=ListingDetailOut)
def get_listing(listing_id: int, db: Annotated[Session, Depends(get_db)]):
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    # build from ListingOut: the detail schema's parking_matches field would
    # otherwise collide with the ORM relationship during model_validate
    base = ListingOut.model_validate(listing)
    base.snippet = (listing.description or "")[:220]
    ms = db.scalars(
        select(ParkingMatch)
        .options(joinedload(ParkingMatch.parking))
        .where(ParkingMatch.listing_id == listing.id)
        .order_by(ParkingMatch.distance_m)
    ).all()
    matches = [_match_out(listing, m) for m in ms]
    out = ListingDetailOut(
        **base.model_dump(),
        description=listing.description or "",
    )
    out.parking_matches = matches
    out.parking_match_count = len(matches)
    if matches:
        out.best_parking = matches[0]
    return out
