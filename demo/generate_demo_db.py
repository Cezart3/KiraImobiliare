"""Build the SQLite database behind the public demo.

Every listing here is INVENTED. Nothing is scraped, nothing comes from a real
listing site, and no real address, phone number or person appears. The ad text
is composed from the templates below, then fed through the app's own extractors
(`app.scraping.extractors`) and matching service — so the demo exercises the
real pipeline, only on made-up input.

Run it before deploying:

    python demo/generate_demo_db.py

It writes `demo/demo.db`, which the Vercel function copies into /tmp on cold
start and serves read-only.
"""
from __future__ import annotations

import os
import random
import sys
from datetime import timedelta
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
REPO_DIR = DEMO_DIR.parent
DB_PATH = DEMO_DIR / "demo.db"

# The engine is built at import time from settings, so point it at the demo file
# before anything from `app` is imported.
sys.path.insert(0, str(REPO_DIR / "backend"))
os.environ["RS_DATABASE_URL"] = f"sqlite:///{DB_PATH.as_posix()}"

from app.core.cities import load_cities  # noqa: E402
from app.db.base import Base, SessionLocal, engine, init_db  # noqa: E402
from app.db.models import (  # noqa: E402
    Listing,
    ParkingSpot,
    ScrapeRun,
    utcnow,
)
from app.scraping.extractors.address import extract_street  # noqa: E402
from app.scraping.extractors.heating import classify_heating  # noqa: E402
from app.scraping.extractors.parking import (  # noqa: E402
    classify_parking,
    classify_parking_spot,
)
from app.scraping.extractors.price import find_price_text, to_eur  # noqa: E402
from app.scraping.extractors.rooms import (  # noqa: E402
    extract_floor,
    extract_rooms,
    extract_surface,
)
from app.services.matching import rebuild_matches  # noqa: E402

SEED = 20260818
LISTING_COUNT = 90      # per city
PARKING_COUNT = 24      # per city

# Rent levels differ enough between these cities that one price table would look
# wrong everywhere except Cluj. Multipliers are rough, and only need to make the
# demo plausible.
CITY_PRICE_FACTOR = {
    "bucuresti": 1.05,
    "cluj-napoca": 1.0,
    "timisoara": 0.85,
    "iasi": 0.8,
    "oradea": 0.75,
    "targu-mures": 0.7,
}

# Where a demo card's "see the original ad" link goes. There is no original ad.
SOURCE_LINK = "https://cezart3.vercel.app/work/kira"

SITES = ["storia", "olx", "imobiliare", "publi24", "lajumate"]

# Streets used in the invented ads. Real Cluj street names, never with a real
# building number attached to a real person or listing.
STREETS = [
    "Calea Mănăștur", "Strada Fabricii", "Bulevardul Muncii", "Strada Aurel Vlaicu",
    "Calea Turzii", "Strada Alverna", "Strada Bucium", "Strada Dorobanților",
    "Strada Observatorului", "Strada Câmpului", "Strada Războieni", "Strada Plopilor",
    "Strada Constantin Brâncuși", "Strada Nicolae Titulescu", "Strada Traian Vuia",
    "Strada Izlazului", "Strada Bună Ziua", "Strada Septimiu Albini",
]

ROOM_PHRASES = {
    0: ["garsonieră", "garsonieră confort 1"],
    1: ["1 cameră", "o cameră"],
    2: ["2 camere", "apartament 2 camere", "apartament cu 2 camere"],
    3: ["3 camere", "apartament 3 camere"],
    4: ["4 camere", "apartament cu 4 camere"],
}

LAYOUTS = ["decomandat", "semidecomandat", "circular", ""]

HEATING_PHRASES = {
    "centrala": [
        "centrală proprie",
        "centrală termică proprie",
        "încălzire cu centrală proprie pe gaz",
        "centrala proprie, calorifere noi",
    ],
    "termoficare": [
        "termoficare",
        "racordat la termoficare",
        "încălzire prin termoficare (RADP)",
    ],
    "unknown": ["", "", "încălzire clasică"],
}

PARKING_PHRASES = {
    "included": [
        "loc de parcare inclus",
        "garaj inclus în preț",
        "parcare subterană inclusă",
        "cu loc de parcare inclus în chirie",
    ],
    "likely": [
        "loc de parcare",
        "beneficiază de parcare",
        "parcare la bloc",
    ],
    "possible": [
        "posibilitate de parcare",
        "parcare în zonă",
        "se poate parca pe stradă",
    ],
    "none": [
        "fără loc de parcare",
        "nu dispune de parcare",
    ],
    "unknown": ["", "", ""],
}

EXTRAS = [
    "mobilat și utilat complet",
    "mobilat modern, utilat nou",
    "nemobilat",
    "renovat recent",
    "bloc nou, finisaje de calitate",
    "termopan, ușă metalică",
    "aer condiționat în living",
    "balcon închis",
    "vedere spre parc",
    "acces rapid la transport în comun",
]

AVAILABILITY = [
    "liber de la 1 septembrie",
    "disponibil imediat",
    "liber de la începutul lunii viitoare",
    "se închiriază pe termen lung",
]

PARKING_TITLES = [
    "Închiriez loc de parcare subteran",
    "Loc parcare exterior, numerotat",
    "Garaj de închiriat",
    "Loc de parcare în parcare supraetajată",
    "Închiriez garaj, acces auto facil",
]

def _price_phrase(rng: random.Random, rooms: int, factor: float) -> str:
    """A price written the way people actually write it, sometimes in lei."""
    base = {0: 300, 1: 330, 2: 430, 3: 560, 4: 720}[rooms]
    eur = int(round((base + rng.randrange(-70, 190, 10)) * factor, -1))
    if rng.random() < 0.22:
        ron = int(round(eur * 5.05, -1))
        raw = f"{ron // 1000}.{ron % 1000:03d}" if ron >= 1000 else str(ron)
        unit = rng.choice(["lei", "RON", "lei/lună"])
        return f"Preț {raw} {unit}"
    style = rng.random()
    if style < 0.3:
        return f"{eur} €"
    if style < 0.6:
        return f"Preț: {eur} euro"
    return f"{eur} EUR/lună"


def _compose_ad(rng: random.Random, zone_name: str, factor: float) -> tuple[str, str, str]:
    """Return (title, description, street_phrase) for one invented listing."""
    rooms = rng.choices([0, 1, 2, 3, 4], weights=[12, 8, 40, 27, 13])[0]
    rooms_phrase = rng.choice(ROOM_PHRASES[rooms])
    layout = rng.choice(LAYOUTS)
    street = rng.choice(STREETS)
    surface = {0: 32, 1: 38, 2: 54, 3: 72, 4: 96}[rooms] + rng.randrange(-6, 18)
    floor_n = rng.randrange(0, 8)
    if floor_n == 0:
        floor_phrase = "parter"
    elif rng.random() < 0.65:
        floor_phrase = f"etaj {floor_n}"
    else:
        # the shorthand people actually type; the extractor does not read it, so
        # these listings end up with no floor — which is what real data looks like
        floor_phrase = f"et. {floor_n}/{rng.randrange(floor_n, 9)}"

    heating_key = rng.choices(
        ["centrala", "termoficare", "unknown"], weights=[58, 27, 15]
    )[0]
    parking_key = rng.choices(
        ["included", "likely", "possible", "none", "unknown"],
        weights=[26, 14, 22, 9, 29],
    )[0]

    title_bits = [f"Închiriez {rooms_phrase}"]
    if layout:
        title_bits.append(layout)
    title_bits.append(f"zona {zone_name}")
    title = ", ".join(title_bits)

    street_phrase = (
        f"pe {street} nr. {rng.randrange(2, 180)}"
        if rng.random() < 0.45
        else f"pe {street}"
    )

    parts = [
        f"Se închiriază {rooms_phrase} {layout}".strip(),
        f"situat {street_phrase}, zona {zone_name}",
        f"{surface} mp",
        floor_phrase,
    ]
    heating_phrase = rng.choice(HEATING_PHRASES[heating_key])
    if heating_phrase:
        parts.append(heating_phrase)
    parking_phrase = rng.choice(PARKING_PHRASES[parking_key])
    if parking_phrase:
        parts.append(parking_phrase)
    parts.extend(rng.sample(EXTRAS, k=rng.randrange(1, 3)))
    parts.append(rng.choice(AVAILABILITY))
    parts.append(_price_phrase(rng, rooms, factor))
    if rng.random() < 0.18:
        parts.append("negociabil")

    description = ", ".join(p for p in parts if p) + "."
    return title, description, street


def _jitter(rng: random.Random, lat: float, lon: float, spread_m: float) -> tuple[float, float]:
    dlat = rng.uniform(-spread_m, spread_m) / 111_320
    dlon = rng.uniform(-spread_m, spread_m) / (111_320 * 0.686)  # cos(46.77°)
    return round(lat + dlat, 6), round(lon + dlon, 6)


def build_listings(rng: random.Random, city) -> list[Listing]:
    factor = CITY_PRICE_FACTOR.get(city.slug, 0.8)
    zones = list(city.zones)
    now = utcnow()
    rows: list[Listing] = []

    for i in range(LISTING_COUNT):
        zone = rng.choice(zones)
        title, description, _street = _compose_ad(rng, zone.name, factor)
        text = f"{title}. {description}"

        # everything below is the app's own extraction logic, on invented text
        rooms = extract_rooms(text)
        surface = extract_surface(text)
        floor = extract_floor(text)
        heating = classify_heating(text)
        parking_status, parking_conf = classify_parking(text)
        price_hit = find_price_text(text)
        price_raw = f"{price_hit[0]} {price_hit[1]}" if price_hit else ""
        price_eur = to_eur(price_raw) if price_hit else None
        street = extract_street(text, city.stop_terms())

        if street and any(ch.isdigit() for ch in street):
            precision, spread = "exact", 260
        elif street:
            precision, spread = "street", 500
        else:
            precision, spread = "zone", 900
        lat, lon = _jitter(rng, zone.lat, zone.lon, spread)

        posted = now - timedelta(
            days=rng.randrange(0, 9), hours=rng.randrange(0, 24), minutes=rng.randrange(0, 60)
        )

        rows.append(
            Listing(
                site=rng.choice(SITES),
                source_id=f"demo-{city.slug}-{i:04d}",
                url=f"{SOURCE_LINK}#anunt-demo-{city.slug}-{i:04d}",
                title=title,
                description=description,
                price_eur=price_eur,
                price_raw=price_raw,
                price_negotiable="negociabil" in description.lower(),
                rooms=rooms,
                surface_m2=surface,
                floor=floor,
                city_slug=city.slug,
                zone_slug=zone.slug,
                in_nearby_town=False,
                town_slug=None,
                location_raw=f"{zone.name}, {city.name}",
                address_extracted=street or "",
                lat=lat,
                lon=lon,
                geo_precision=precision,
                parking_status=parking_status.value,
                parking_confidence=parking_conf,
                heating=heating.value,
                images=[],
                posted_at=posted,
                first_seen_at=posted,
                last_seen_at=now - timedelta(minutes=rng.randrange(0, 90)),
                dedup_group=None,
            )
        )
    return rows


def build_parking(rng: random.Random, city) -> list[ParkingSpot]:
    zones = list(city.zones)
    now = utcnow()
    rows: list[ParkingSpot] = []

    for i in range(PARKING_COUNT):
        zone = rng.choice(zones)
        title = rng.choice(PARKING_TITLES)
        numbered = rng.random() < 0.5
        description = ", ".join(
            [
                f"{title.lower()} în zona {zone.name}",
                "loc numerotat" if numbered else "acces liber",
                rng.choice(["acces cu telecomandă", "acces cu cartelă", "curte închisă", "supraveghere video"]),
                f"{rng.randrange(30, 90, 5)} euro",
            ]
        )
        text = f"{title}. {description}"
        kind, is_numbered = classify_parking_spot(text)
        price_hit = find_price_text(text)
        lat, lon = _jitter(rng, zone.lat, zone.lon, 700)

        rows.append(
            ParkingSpot(
                site=rng.choice(SITES),
                url=f"{SOURCE_LINK}#parcare-demo-{city.slug}-{i:03d}",
                title=title,
                description=description,
                price_eur=to_eur(f"{price_hit[0]} {price_hit[1]}") if price_hit else None,
                city_slug=city.slug,
                zone_slug=zone.slug,
                address_extracted="",
                lat=lat,
                lon=lon,
                geo_precision="zone",
                kind=kind.value,
                is_numbered=is_numbered,
                first_seen_at=now - timedelta(days=rng.randrange(0, 12)),
                last_seen_at=now - timedelta(hours=rng.randrange(0, 20)),
            )
        )
    return rows


def main() -> None:
    rng = random.Random(SEED)

    if DB_PATH.exists():
        DB_PATH.unlink()
    for suffix in ("-wal", "-shm"):
        stale = DB_PATH.with_name(DB_PATH.name + suffix)
        if stale.exists():
            stale.unlink()

    init_db()
    Base.metadata.create_all(engine)

    # every city the app offers gets data — the city picker on the landing page
    # lists all of them, and a demo that empties itself on the second click is
    # worse than no demo
    matched_total = 0
    for city in load_cities().values():
        with SessionLocal() as db:
            listings = build_listings(rng, city)
            parking = build_parking(rng, city)
            db.add_all(listings)
            db.add_all(parking)
            db.flush()

            db.add(
                ScrapeRun(
                    site="demo",
                    city_slug=city.slug,
                    kind="rent",
                    started_at=utcnow() - timedelta(minutes=12),
                    finished_at=utcnow() - timedelta(minutes=1),
                    status="ok",
                    items_found=len(listings),
                    items_upserted=len(listings),
                )
            )
            db.commit()

            matched_total += rebuild_matches(db, city)
            db.commit()

    with SessionLocal() as db:
        total = db.query(Listing).count()
        with_price = db.query(Listing).filter(Listing.price_eur.isnot(None)).count()
        own_boiler = db.query(Listing).filter(Listing.heating == "centrala_proprie").count()
        parking_incl = db.query(Listing).filter(Listing.parking_status == "included").count()
        spots = db.query(ParkingSpot).count()
        cities = db.query(Listing.city_slug).distinct().count()

    print(f"wrote {DB_PATH}")
    print(f"  cities            {cities}")
    print(f"  listings          {total}")
    print(f"  price extracted   {with_price}")
    print(f"  own boiler        {own_boiler}")
    print(f"  parking included  {parking_incl}")
    print(f"  parking spots     {spots}")
    print(f"  parking matches   {matched_total}")


if __name__ == "__main__":
    main()
