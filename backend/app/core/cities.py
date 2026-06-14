"""City / zone / nearby-town configuration, loaded from app/data/cities/*.json.

JSON is the source of truth (versioned in git). Aliases are matched on
diacritics-folded text with word boundaries (avoids e.g. 'iasi' matching
inside 'chiriasi').
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import DATA_DIR
from app.core.textutil import fold

_CITIES_DIR = DATA_DIR / "cities"


@dataclass(frozen=True)
class Place:
    slug: str
    name: str
    aliases: tuple[str, ...]          # folded
    patterns: tuple[re.Pattern, ...]  # \b-bounded, on folded text
    lat: float
    lon: float


@dataclass(frozen=True)
class CityConfig:
    slug: str
    name: str
    county: str
    aliases: tuple[str, ...]
    patterns: tuple[re.Pattern, ...]
    lat: float
    lon: float
    radius_km: float
    sites: dict
    zones: tuple[Place, ...]
    nearby_towns: tuple[Place, ...]
    landmarks: tuple[Place, ...]   # well-known reference points (malls, etc.)

    def stop_terms(self) -> frozenset[str]:
        """City-name tokens, used to truncate street extraction."""
        toks: set[str] = set()
        for a in self.aliases:
            toks.update(a.split())
        return frozenset(toks)


def _mk_patterns(aliases: tuple[str, ...]) -> tuple[re.Pattern, ...]:
    return tuple(re.compile(rf"\b{re.escape(a)}\b") for a in aliases)


def _alias_set(name: str, slug: str, extra: list[str]) -> tuple[str, ...]:
    out = {fold(name), slug.replace("-", " "), *(fold(a) for a in extra)}
    return tuple(sorted(a for a in out if a))


def _place(d: dict) -> Place:
    aliases = _alias_set(d["name"], d["slug"], d.get("aliases", []))
    return Place(
        slug=d["slug"], name=d["name"], aliases=aliases,
        patterns=_mk_patterns(aliases), lat=d["lat"], lon=d["lon"],
    )


@lru_cache(maxsize=1)
def load_cities() -> dict[str, CityConfig]:
    out: dict[str, CityConfig] = {}
    for path in sorted(_CITIES_DIR.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        aliases = _alias_set(d["name"], d["slug"], d.get("aliases", []))
        out[d["slug"]] = CityConfig(
            slug=d["slug"], name=d["name"], county=d.get("county", ""),
            aliases=aliases, patterns=_mk_patterns(aliases),
            lat=d["center"]["lat"], lon=d["center"]["lon"],
            radius_km=d.get("radius_km", 7),
            sites=d.get("sites", {}),
            zones=tuple(_place(z) for z in d.get("zones", [])),
            nearby_towns=tuple(_place(t) for t in d.get("nearby_towns", [])),
            landmarks=tuple(_place(lm) for lm in d.get("landmarks", [])),
        )
    return out


def get_city(slug: str) -> CityConfig:
    return load_cities()[slug]


def _find_place(places: tuple[Place, ...], *texts: str | None) -> Place | None:
    """Check texts in priority order (location field first, then title, etc.)."""
    for text in texts:
        if not text:
            continue
        ft = fold(text)
        for p in places:
            if any(rx.search(ft) for rx in p.patterns):
                return p
    return None


def find_zone(city: CityConfig, *texts: str | None) -> Place | None:
    return _find_place(city.zones, *texts)


def find_town(city: CityConfig, *texts: str | None) -> Place | None:
    return _find_place(city.nearby_towns, *texts)


def find_landmark(city: CityConfig, *texts: str | None) -> Place | None:
    """A known reference point named in the text (e.g. 'zona Kaufland Mărăști').
    More specific than the zone centroid, less than a full street address."""
    return _find_place(city.landmarks, *texts)


# Out-of-area RO towns/cities that are NOT target cities and NOT anyone's
# nearby_town — agency/site feeds sometimes file these under a target city
# (e.g. a Campia Turzii or Baia Mare flat showing up under Cluj). Checked on
# folded text with word boundaries, against BOTH the location field and the
# title (the real town is often only in the title). Verified at load time not
# to collide with any configured nearby_town.
_FOREIGN_TOWNS = (
    "campia turzii", "baia mare", "brasov", "constanta", "sibiu", "craiova",
    "ploiesti", "galati", "braila", "arad", "pitesti", "suceava", "buzau",
    "satu mare", "ramnicu valcea", "drobeta", "focsani", "bacau", "botosani",
    "piatra neamt", "deva", "hunedoara", "resita", "slatina", "alba iulia",
    "bistrita", "calarasi", "giurgiu", "alexandria", "vaslui", "tulcea",
    "slobozia", "zalau", "sfantu gheorghe", "miercurea ciuc", "turda", "dej",
    "gherla", "huedin",
)
_FOREIGN_RE = tuple(re.compile(rf"\b{re.escape(t)}\b") for t in _FOREIGN_TOWNS)
# street-type prefixes — a foreign town name right after one of these is a
# STREET/SQUARE named after a city, not the locality (e.g. "Strada Craiova",
# "Bld. Timisoara", "Piata Alba Iulia"). Used to avoid false out-of-area drops.
_STREET_PREFIX = (
    r"strada", r"str\.?", r"bulevardul", r"bdul", r"bd\.?", r"b-?dul",
    r"blvd\.?", r"calea", r"aleea", r"piata", r"pta\.?", r"soseaua", r"sos\.?",
    r"intrarea", r"splaiul",
)
_FOREIGN_AS_STREET = tuple(
    re.compile(rf"\b(?:{'|'.join(_STREET_PREFIX)})\s+{re.escape(t)}\b")
    for t in _FOREIGN_TOWNS
)


def mentions_other_city(text: str | None, current_slug: str) -> bool:
    """True when `text` (the structured location field) names a DIFFERENT target
    city, or a known out-of-area town that isn't part of the current city. The
    caller still allows it through if `find_town` matches a configured
    nearby_town.

    A foreign-town name immediately preceded by a street word (e.g. "Strada
    Craiova", "Piata Alba Iulia") is treated as a street/square, NOT the
    locality, so legit in-city listings aren't dropped. Pass only the structured
    location field here — NOT free-text titles, whose street/square names are too
    easily confused with city names."""
    if not text:
        return False
    ft = fold(text)
    for slug, cfg in load_cities().items():
        if slug == current_slug:
            continue
        if any(rx.search(ft) for rx in cfg.patterns):
            return True
    # an out-of-area town, but not when it's clearly a street/square name
    for town_rx, street_rx in zip(_FOREIGN_RE, _FOREIGN_AS_STREET, strict=True):
        if town_rx.search(ft) and not street_rx.search(ft):
            return True
    return False
