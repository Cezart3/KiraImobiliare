from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.cities import load_cities
from app.core.config import settings
from app.db.models import Listing, ParkingSpot, ScrapeRun, utcnow
from app.schemas.meta import CityOut, CityStatsOut, PlaceOut, SiteRunOut

router = APIRouter(tags=["meta"])


@router.get("/cities", response_model=list[CityOut])
def cities():
    out = []
    for cfg in load_cities().values():
        out.append(
            CityOut(
                slug=cfg.slug,
                name=cfg.name,
                zones=[PlaceOut(slug=z.slug, name=z.name) for z in cfg.zones],
                nearby_towns=[PlaceOut(slug=t.slug, name=t.name) for t in cfg.nearby_towns],
                sites=sorted(cfg.sites.keys()),
            )
        )
    return out


@router.get("/stats", response_model=list[CityStatsOut])
def stats(db: Annotated[Session, Depends(get_db)]):
    cutoff = utcnow() - timedelta(days=settings.listing_active_days)
    out = []
    for slug in load_cities():
        active = db.scalar(
            select(func.count()).where(
                Listing.city_slug == slug, Listing.last_seen_at >= cutoff
            )
        ) or 0
        active_p = db.scalar(
            select(func.count()).where(
                ParkingSpot.city_slug == slug, ParkingSpot.last_seen_at >= cutoff
            )
        ) or 0
        runs = db.scalars(
            select(ScrapeRun)
            .where(ScrapeRun.city_slug == slug)
            .order_by(ScrapeRun.started_at.desc())
            .limit(12)
        ).all()
        seen: set[tuple[str, str]] = set()
        last_runs = []
        for r in runs:
            key = (r.site, r.kind)
            if key in seen:
                continue
            seen.add(key)
            last_runs.append(
                SiteRunOut(
                    site=r.site,
                    kind=r.kind,
                    status=r.status,
                    finished_at=r.finished_at,
                    items_found=r.items_found,
                    items_upserted=r.items_upserted,
                )
            )
        out.append(
            CityStatsOut(
                city_slug=slug,
                active_listings=active,
                active_parking=active_p,
                last_runs=last_runs,
            )
        )
    return out
