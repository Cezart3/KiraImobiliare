"""Geocode unverified zones/towns in app/data/cities/*.json via Nominatim.

For every zone/town with verified=false, queries Nominatim with
q="{name}, {city name}, Romania" and, on a hit within radius_km*2 of the
city center, updates lat/lon and sets verified=true. On a miss (no result,
or result too far from center), leaves the entry untouched and prints the
miss for manual follow-up.

Run with: .venv\\Scripts\\python.exe tools\\geocode_zones.py
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import requests

# Windows consoles default to cp1252, which can't print Romanian diacritics.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

CITIES_DIR = Path(__file__).resolve().parent.parent / "app" / "data" / "cities"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "RentScalper/0.1 (personal project)"
SLEEP_SECONDS = 1.1


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def geocode(query: str) -> tuple[float, float] | None:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": 1,
                "countrycodes": "ro",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"    ERROR querying '{query}': {exc}")
        return None
    if not data:
        return None
    item = data[0]
    return float(item["lat"]), float(item["lon"])


def main() -> None:
    total_unverified = 0
    verified_count = 0
    misses: list[str] = []

    for path in sorted(CITIES_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        city_name = data["name"]
        center = data["center"]
        radius_km = data.get("radius_km", 7)
        max_dist = radius_km * 2
        changed = False

        for kind in ("zones", "nearby_towns"):
            for place in data.get(kind, []):
                if place.get("verified", False):
                    continue
                total_unverified += 1
                query = f"{place['name']}, {city_name}, Romania"
                print(f"[{path.stem}] {kind}/{place['slug']}: querying '{query}'")
                time.sleep(SLEEP_SECONDS)
                result = geocode(query)

                if result is None:
                    print("    MISS: no result")
                    misses.append(f"{path.stem}/{kind}/{place['slug']}")
                    continue

                lat, lon = result
                dist = haversine_km(center["lat"], center["lon"], lat, lon)
                if dist > max_dist:
                    print(f"    MISS: result ({lat}, {lon}) is {dist:.1f}km from center (> {max_dist}km)")
                    misses.append(f"{path.stem}/{kind}/{place['slug']}")
                    continue

                place["lat"] = lat
                place["lon"] = lon
                place["verified"] = True
                verified_count += 1
                changed = True
                print(f"    OK: ({lat}, {lon}), {dist:.1f}km from center")

        if changed:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print(f"  -> wrote {path.name}")

    print()
    print("=== SUMMARY ===")
    print(f"total unverified zones/towns checked: {total_unverified}")
    print(f"verified: {verified_count}")
    print(f"misses ({len(misses)}): {misses}")


if __name__ == "__main__":
    main()
