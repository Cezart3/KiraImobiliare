"""Re-pin listings that are stuck at zone/city precision using known landmarks
found in their stored title/description. No network: landmark coords are local.

Run after adding landmarks to a city's JSON.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import or_, select  # noqa: E402

from app.core.cities import find_landmark, get_city, load_cities  # noqa: E402
from app.db.base import SessionLocal  # noqa: E402
from app.db.models import GeoPrecision, Listing  # noqa: E402

WEAK = (GeoPrecision.ZONE.value, GeoPrecision.CITY.value, GeoPrecision.NONE.value)

with SessionLocal() as db:
    moved = 0
    for slug in load_cities():
        city = get_city(slug)
        if not city.landmarks:
            continue
        rows = db.scalars(
            select(Listing).where(
                Listing.city_slug == slug,
                Listing.geo_precision.in_(WEAK),
                Listing.in_nearby_town.is_(False),
                or_(Listing.title.is_not(None), Listing.description.is_not(None)),
            )
        ).all()
        for r in rows:
            lm = find_landmark(city, r.title, r.location_raw, r.description)
            if lm is None:
                continue
            r.lat, r.lon = lm.lat, lm.lon
            r.geo_precision = GeoPrecision.LANDMARK.value
            if not r.address_extracted or r.address_extracted == city.name:
                r.address_extracted = f"lângă {lm.name}"
            moved += 1
        db.commit()
    print(f"re-pinned {moved} listings to a landmark")
