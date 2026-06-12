import math
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.db.models import Listing, ParkingMatch, User, utcnow
from app.schemas.listing import (
    ListingDetailOut,
    ListingOut,
    ListingPage,
    ParkingMatchOut,
    ParkingSpotOut,
)
from app.services.geo import maps_walk_link

router = APIRouter(tags=["listings"])

_STATUS_FILTERS = {"included", "likely_included", "area_possible", "none", "unknown"}


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
    user: Annotated[User | None, Depends(get_current_user)] = None,
    price_min: float | None = None,
    price_max: float | None = None,
    rooms: Annotated[list[int] | None, Query()] = None,
    zones: Annotated[list[str] | None, Query()] = None,
    heating: Annotated[list[str] | None, Query()] = None,
    parking: Annotated[list[str] | None, Query()] = None,
    sites: Annotated[list[str] | None, Query()] = None,
    q: str | None = None,
    include_nearby: bool = False,
    sort: Annotated[str, Query(pattern="^(newest|price_asc|price_desc|parking)$")] = "newest",
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

    # freemium paywall: free users see the first N results but the real total
    locked = False
    visible_limit: int | None = None
    if settings.paywall_enabled and not (user is not None and user.has_access()):
        visible_limit = settings.free_listing_limit
        page = 1
        page_size = min(page_size, visible_limit)
        locked = total > visible_limit

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
        items.append(out)

    return ListingPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=1 if visible_limit is not None else max(1, math.ceil(total / page_size)),
        locked=locked,
        visible_limit=visible_limit,
    )


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
