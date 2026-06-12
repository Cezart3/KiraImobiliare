"""Enrich image-less/thin listings straight from the DB (independent of scrape runs).

Usage (from backend/): .venv\\Scripts\\python.exe tools\\backfill_details.py [--limit 100]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import or_, select  # noqa: E402

import app.scraping.sites  # noqa: F401, E402  (register adapters)
from app.core.cities import get_city  # noqa: E402
from app.db.base import SessionLocal, init_db  # noqa: E402
from app.db.models import Listing  # noqa: E402
from app.scraping.base import REGISTRY, RawListing  # noqa: E402
from app.scraping.pipeline import apply_extractions, drop_reason_rent  # noqa: E402
from app.services.geo import Geocoder  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    init_db()
    with SessionLocal() as db:
        rows = db.scalars(
            select(Listing)
            .where(or_(Listing.images == [], Listing.images.is_(None)))
            .order_by(Listing.last_seen_at.desc())
            .limit(args.limit)
        ).all()
        print(f"backfilling {len(rows)} listings without images")
        geocoder = Geocoder(db, budget=20)
        enriched = dropped = failed = 0
        for listing in rows:
            scraper = REGISTRY.get(listing.site)
            if scraper is None:
                continue
            raw = RawListing(
                site=listing.site,
                url=listing.url,
                title=listing.title,
                description=listing.description or "",
            )
            raw = scraper.fetch_detail(raw)
            if not raw.images and len(raw.description) <= len(listing.description or ""):
                failed += 1
                continue
            reason = drop_reason_rent(raw, listing.price_eur)
            if reason:
                db.delete(listing)
                db.commit()
                dropped += 1
                print(f"  dropped ({reason}): {listing.title[:50]}")
                continue
            apply_extractions(listing, raw, get_city(listing.city_slug), geocoder)
            db.commit()
            enriched += 1
        print(f"done: enriched={enriched} dropped={dropped} no-data={failed}")


if __name__ == "__main__":
    main()
