"""Local scrape control: a button in the UI starts a fresh scrape for one city.

Local-tool only — no auth. A process-wide lock ensures one scrape at a time so
a user can't launch several at once. Progress is reported via a simple in-memory
status the UI polls.
"""
import threading
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.cities import load_cities
from app.db.models import Listing, ScrapeRun, utcnow
from app.worker.jobs import run_scrape_city

router = APIRouter(tags=["scrape"])

# one scrape at a time, shared across requests
_lock = threading.Lock()
_state: dict = {"running": False, "city": None, "started_at": None, "summary": None, "error": None}


class ScrapeStart(BaseModel):
    city: str
    max_pages: int | None = None


def _run(city_slug: str, max_pages: int | None) -> None:
    try:
        summary = run_scrape_city(city_slug, max_pages=max_pages)
        _state["summary"] = summary
        _state["error"] = None
    except Exception as e:  # noqa: BLE001
        _state["error"] = f"{type(e).__name__}: {e}"
    finally:
        _state["running"] = False
        _lock.release()


@router.post("/scrape")
def start_scrape(body: ScrapeStart):
    """Kick off a fresh scrape for one city (runs in the background)."""
    if body.city not in load_cities():
        raise HTTPException(status_code=404, detail=f"Oraș necunoscut: {body.city}")
    if not _lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="O actualizare este deja în curs.")
    _state.update(
        running=True, city=body.city, started_at=utcnow().isoformat(),
        summary=None, error=None,
    )
    t = threading.Thread(
        target=_run, kwargs={"city_slug": body.city, "max_pages": body.max_pages},
        daemon=True, name=f"scrape-{body.city}",
    )
    t.start()
    return {"started": True, "city": body.city}


@router.get("/scrape/status")
def scrape_status(db: Annotated[Session, Depends(get_db)]):
    """Current scrape state + last run rows so the UI can show progress."""
    runs = []
    if _state.get("city"):
        rows = db.query(ScrapeRun).filter(
            ScrapeRun.city_slug == _state["city"]
        ).order_by(ScrapeRun.started_at.desc()).limit(12).all()
        seen = set()
        for r in rows:
            key = (r.site, r.kind)
            if key in seen:
                continue
            seen.add(key)
            runs.append({
                "site": r.site, "kind": r.kind, "status": r.status,
                "found": r.items_found, "upserted": r.items_upserted,
            })
    return {
        "running": _state["running"],
        "city": _state["city"],
        "error": _state["error"],
        "summary": _state["summary"],
        "recent_runs": runs,
    }


@router.get("/scrape/has-data")
def has_data(city: str, db: Annotated[Session, Depends(get_db)]) -> dict:
    """Whether a city already has any listings — UI uses it to decide between the
    'first run' empty state and the normal grid."""
    n = db.query(Listing).filter(Listing.city_slug == city).count()
    return {"city": city, "count": n}
