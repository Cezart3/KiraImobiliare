"""Scrape jobs: per-city scrape -> upsert -> detail enrichment -> parking matching."""
import logging

import app.scraping.sites  # noqa: F401  (register site adapters)
from app.core.cities import CityConfig, get_city
from app.core.config import settings
from app.db.base import SessionLocal, init_db
from app.db.models import ScrapeRun, utcnow
from app.scraping.base import REGISTRY, SiteScraper
from app.scraping.pipeline import (
    apply_extractions,
    drop_reason_rent,
    upsert_parking,
    upsert_rental,
)
from app.services.geo import Geocoder
from app.services.matching import rebuild_matches

log = logging.getLogger(__name__)

# parking words worth a full-description fetch when the status is still weak
_PARKING_HINT = ("parcare", "garaj", "parking")
_WEAK_PARKING = {"unknown", "likely_included"}


def _needs_enrich(obj) -> bool:
    if len(obj.description or "") < 200 or not obj.images:
        return True
    # parking still ambiguous but the title/snippet mentions parking -> the
    # decisive phrase is likely folded inside the full description
    if obj.parking_status in _WEAK_PARKING:
        hay = f"{obj.title} {obj.description}".lower()
        if any(w in hay for w in _PARKING_HINT):
            return True
    return False


def _scrape_kind(
    db, scraper: SiteScraper, city: CityConfig, geocoder: Geocoder, kind: str, pages: int
) -> dict:
    run = ScrapeRun(site=scraper.site, city_slug=city.slug, kind=kind)
    db.add(run)
    db.commit()

    found = upserted = dropped = 0
    enrich_queue = []
    try:
        items = (
            scraper.iter_rentals(city, pages)
            if kind == "rent"
            else scraper.iter_parking(city, pages)
        )
        for raw in items:
            found += 1
            if kind == "rent":
                obj, created, drop = upsert_rental(db, raw, city, geocoder)
            else:
                obj, created, drop = upsert_parking(
                    db, raw, city, geocoder,
                    category_trusted=scraper.parking_category_trusted,
                )
            if drop:
                dropped += 1
                continue
            upserted += 1
            # enrich anything thin — also OLD rows that never got their detail
            # fetch (budget caps each run; backfill completes across runs).
            # Also enrich when parking is still ambiguous but the title/snippet
            # hints at parking: sites (esp. storia) hide "loc de parcare inclus
            # in pret" in the full description behind a "see more" fold, so the
            # short snippet alone misclassifies it as merely "likely".
            if kind == "rent" and obj is not None and _needs_enrich(obj):
                enrich_queue.append((raw, obj))
            if found % 50 == 0:
                db.commit()
        db.commit()

        for raw, listing in enrich_queue[: settings.detail_fetch_budget]:
            enriched = scraper.fetch_detail(raw)
            # the full description may reveal a short-stay / parking-only ad
            # that the list snippet hid — drop it instead of enriching
            reason = drop_reason_rent(enriched, listing.price_eur)
            if reason:
                db.delete(listing)
                db.commit()
                dropped += 1
                upserted -= 1
                continue
            apply_extractions(listing, enriched, city, geocoder)
            db.commit()
        run.status = "ok"
    except Exception as e:  # keep other sites running
        db.rollback()
        run.status = "error"
        run.error = f"{type(e).__name__}: {e}"[:1000]
        log.exception("scrape failed: %s/%s/%s", scraper.site, city.slug, kind)

    run.items_found = found
    run.items_upserted = upserted
    run.finished_at = utcnow()
    db.commit()
    return {"found": found, "upserted": upserted, "dropped": dropped, "status": run.status}


def run_scrape_city(
    city_slug: str, only_site: str | None = None, max_pages: int | None = None
) -> dict:
    init_db()
    city = get_city(city_slug)
    pages = max_pages or settings.max_pages_per_site
    summary: dict = {}
    with SessionLocal() as db:
        geocoder = Geocoder(db)
        for site, scraper in REGISTRY.items():
            if only_site and site != only_site:
                continue
            if not scraper.is_enabled(city):
                continue
            summary[site] = {"rent": _scrape_kind(db, scraper, city, geocoder, "rent", pages)}
            if scraper.supports_parking:
                summary[site]["parking"] = _scrape_kind(
                    db, scraper, city, geocoder, "parking", max(2, pages // 2)
                )
        summary["parking_matches"] = rebuild_matches(db, city)
    log.info("scrape %s done: %s", city_slug, summary)
    return summary
