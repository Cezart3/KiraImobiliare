"""Distance helpers + Nominatim geocoding with DB cache and per-run budget."""
import logging
import math
import re
import time

import requests
from sqlalchemy.orm import Session

from app.core.cities import CityConfig
from app.core.config import settings
from app.db.models import GeoCache

log = logging.getLogger(__name__)

_NR_RE = re.compile(r"\bnr\.?\s*", re.I)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def walk_minutes(distance_m: float) -> float:
    """Straight-line distance -> estimated on-foot minutes (detour factor applied)."""
    meters = distance_m * settings.walk_detour_factor
    return round(meters / 1000.0 / settings.walk_speed_kmh * 60.0, 1)


def maps_walk_link(olat: float, olon: float, dlat: float, dlon: float) -> str:
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&origin={olat},{olon}&destination={dlat},{dlon}&travelmode=walking"
    )


class Geocoder:
    """Nominatim with a persistent DB cache. Respects 1 req/s and a per-run budget."""

    def __init__(self, db: Session, budget: int | None = None):
        self.db = db
        self.budget = settings.geocode_budget_per_run if budget is None else budget
        self._last_call = 0.0

    def geocode(self, addr: str, city: CityConfig) -> tuple[float, float] | None:
        addr = _NR_RE.sub("", " ".join((addr or "").split())).strip(" ,.")
        if not addr:
            return None
        query = f"{addr}, {city.name}, Romania"

        row = self.db.get(GeoCache, query)
        if row is not None:
            return (row.lat, row.lon) if row.found else None
        if self.budget <= 0:
            return None

        wait = 1.1 - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()
        self.budget -= 1

        dlat = city.radius_km / 111.0 * 1.4
        dlon = city.radius_km / (111.0 * math.cos(math.radians(city.lat))) * 1.4
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "ro",
            "viewbox": f"{city.lon - dlon},{city.lat + dlat},{city.lon + dlon},{city.lat - dlat}",
            "bounded": 1,
        }
        found: tuple[float, float] | None = None
        try:
            r = requests.get(
                settings.nominatim_url,
                params=params,
                timeout=20,
                headers={"User-Agent": "Kira/1.0 (local rental-search tool; personal use)"},
            )
            data = r.json()
            if data:
                found = (float(data[0]["lat"]), float(data[0]["lon"]))
        except (requests.RequestException, ValueError, KeyError, IndexError) as e:
            log.warning("geocode failed for %r: %s", query, e)
            return None  # transient failure: do not cache

        self.db.add(
            GeoCache(
                query=query,
                lat=found[0] if found else None,
                lon=found[1] if found else None,
                found=found is not None,
            )
        )
        self.db.flush()
        return found
