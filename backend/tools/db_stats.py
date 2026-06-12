"""Quick DB overview: python tools/db_stats.py (run from backend/)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select  # noqa: E402

from app.db.base import SessionLocal  # noqa: E402
from app.db.models import GeoCache, Listing, ParkingMatch, ParkingSpot  # noqa: E402

with SessionLocal() as db:
    print("listings per city/site:")
    rows = db.execute(
        select(Listing.city_slug, Listing.site, func.count())
        .group_by(Listing.city_slug, Listing.site)
        .order_by(Listing.city_slug, func.count().desc())
    ).all()
    for city, site, n in rows:
        print(f"  {city:14} {site:12} {n}")
    print("parking spots per city:")
    for city, n in db.execute(
        select(ParkingSpot.city_slug, func.count()).group_by(ParkingSpot.city_slug)
    ).all():
        print(f"  {city:14} {n}")
    print("matches:", db.scalar(select(func.count()).select_from(ParkingMatch)))
    print("geo cache entries:", db.scalar(select(func.count()).select_from(GeoCache)))
    print("parking status distribution:")
    for status, n in db.execute(
        select(Listing.parking_status, func.count()).group_by(Listing.parking_status)
    ).all():
        print(f"  {status:18} {n}")
    print("heating distribution:")
    for heating, n in db.execute(
        select(Listing.heating, func.count()).group_by(Listing.heating)
    ).all():
        print(f"  {heating:18} {n}")
