"""Admin endpoints: scrape trigger + operational stats.

Access: allowed when RS_ENABLE_ADMIN_ENDPOINTS=true (dev), or — with it off in
production — when the request carries X-Admin-Token matching RS_ADMIN_TOKEN.
"""
import secrets
import threading
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import ratelimit
from app.core.cities import load_cities
from app.core.config import settings
from app.db.models import Listing, ParkingMatch, ParkingSpot, ScrapeRun, User, utcnow
from app.worker.jobs import run_scrape_city

router = APIRouter(tags=["admin"])


def _check_admin(request: Request) -> None:
    if settings.enable_admin_endpoints:
        return
    token = request.headers.get("x-admin-token", "")
    if settings.admin_token and secrets.compare_digest(token, settings.admin_token):
        return
    raise HTTPException(status_code=403, detail="Admin endpoints disabled")


class ScrapeRequest(BaseModel):
    city: str
    site: str | None = None
    max_pages: int | None = None


@router.post("/admin/scrape")
def trigger_scrape(req: ScrapeRequest, request: Request):
    _check_admin(request)
    ratelimit.enforce(request, "admin-scrape", 10)
    if req.city not in load_cities():
        raise HTTPException(status_code=404, detail=f"Unknown city: {req.city}")
    t = threading.Thread(
        target=run_scrape_city,
        kwargs={"city_slug": req.city, "only_site": req.site, "max_pages": req.max_pages},
        daemon=True,
        name=f"scrape-{req.city}",
    )
    t.start()
    return {"started": True, "city": req.city, "site": req.site}


@router.get("/admin/stats")
def stats(request: Request, db: Annotated[Session, Depends(get_db)]):
    """Operational dashboard: listing counts, per-source freshness (detects dead
    adapters), scrape failures, user/subscriber counts."""
    _check_admin(request)
    now = utcnow()
    active_cutoff = now - timedelta(days=settings.listing_active_days)

    active_by_city = dict(
        db.execute(
            select(Listing.city_slug, func.count())
            .where(Listing.last_seen_at >= active_cutoff)
            .group_by(Listing.city_slug)
        ).all()
    )
    freshness = [
        {
            "city": city,
            "site": site,
            "active": count,
            "newest_seen_min_ago": round((now - last_seen).total_seconds() / 60),
        }
        for city, site, count, last_seen in db.execute(
            select(
                Listing.city_slug,
                Listing.site,
                func.count(),
                func.max(Listing.last_seen_at),
            )
            .where(Listing.last_seen_at >= active_cutoff)
            .group_by(Listing.city_slug, Listing.site)
            .order_by(Listing.city_slug, Listing.site)
        ).all()
    ]
    runs_24h = db.execute(
        select(ScrapeRun.status, func.count())
        .where(ScrapeRun.started_at >= now - timedelta(hours=24))
        .group_by(ScrapeRun.status)
    ).all()
    failures = [
        {
            "city": r.city_slug,
            "site": r.site,
            "kind": r.kind,
            "at": r.started_at.isoformat(),
            "error": (r.error or "")[:200],
        }
        for r in db.scalars(
            select(ScrapeRun)
            .where(
                ScrapeRun.status == "error",
                ScrapeRun.started_at >= now - timedelta(hours=24),
            )
            .order_by(ScrapeRun.started_at.desc())
            .limit(10)
        ).all()
    ]
    return {
        "listings_active": sum(active_by_city.values()),
        "listings_active_by_city": active_by_city,
        "listings_total": db.scalar(select(func.count()).select_from(Listing)) or 0,
        "parking_spots": db.scalar(select(func.count()).select_from(ParkingSpot)) or 0,
        "parking_matches": db.scalar(select(func.count()).select_from(ParkingMatch)) or 0,
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "subscribers": db.scalar(
            select(func.count()).select_from(User).where(User.sub_status == "active")
        )
        or 0,
        "source_freshness": freshness,
        "scrape_runs_24h": {status: n for status, n in runs_24h},
        "scrape_failures_24h": failures,
    }
