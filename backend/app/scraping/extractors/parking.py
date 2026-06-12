"""Parking classification from Romanian listing text.

Taxonomy (user-facing filters):
- INCLUDED         : parking/garage is part of the rental
- LIKELY_INCLUDED  : parking mentioned as amenity, not fully explicit
- AREA_POSSIBLE    : 'posibilitate de parcare', street/free/unmarked parking in the
                     area, or parking available at extra cost
- NONE             : explicitly without parking
- UNKNOWN          : no signal

All patterns run on diacritics-folded lowercase text (see textutil.fold).
"""
import re

from app.core.textutil import fold
from app.db.models import ParkingKind, ParkingStatus

_NONE = [
    r"fara (?:loc de )?parcare",
    r"nu (?:are|exista|include|detine) (?:loc de )?parcare",
]
_EXTRA_COST = [
    r"parcare contra cost",
    r"parcare cu plata",
    r"parcare optionala?",
    r"(?:loc de )?parcare .{0,14}(?:cost suplimentar|extra cost|se plateste)",
]
_STRONG = [
    r"(?:loc(?:ul)? de )?parcare inclus",
    r"garaj inclus",
    r"loc de parcare propriu",
    r"parcare propri[ea]",
    r"include \w{0,15}\s?parcare",
    r"cu loc de parcare",
    r"cu garaj",
    r"loc (?:de )?parcare subteran",
    r"parcare subteran",
    r"(?:loc de )?parcare (?:in|la) pret",
]
_AREA = [
    r"posibilitat\w* (?:de )?parcare",
    r"parcare (?:in|prin) zona",
    r"parcare pe strada",
    r"parcare la liber",
    r"locuri? nemarcat",
    r"parcare nemarcat",
    r"se gaseste parcare",
    r"parcare gratuita in zona",
    r"parcare in fata blocului",
    r"parcare langa bloc",
]
_WEAK = [
    r"loc de parcare",
    r"\bgaraj\b",
    r"parcare\s*\+",
]
_ANY = re.compile(r"parcare|garaj")
_INCLUS = re.compile(r"inclus")

_NONE_RE = [re.compile(p) for p in _NONE]
_EXTRA_RE = [re.compile(p) for p in _EXTRA_COST]
_STRONG_RE = [re.compile(p) for p in _STRONG]
_AREA_RE = [re.compile(p) for p in _AREA]
_WEAK_RE = [re.compile(p) for p in _WEAK]


def classify_parking(text: str, structured_hint: bool = False) -> tuple[ParkingStatus, int]:
    """Return (status, confidence 0-3).

    structured_hint: site provided a structured GARAGE/PARKING tag (e.g. storia tags).
    """
    t = fold(" ".join((text or "").split()))
    if not t:
        status, conf = ParkingStatus.UNKNOWN, 0
    elif any(r.search(t) for r in _NONE_RE):
        status, conf = ParkingStatus.NONE, 3
    elif any(r.search(t) for r in _EXTRA_RE) and not _INCLUS.search(t):
        status, conf = ParkingStatus.AREA_POSSIBLE, 2
    elif any(r.search(t) for r in _STRONG_RE):
        status, conf = ParkingStatus.INCLUDED, 3
    elif any(r.search(t) for r in _AREA_RE):
        status, conf = ParkingStatus.AREA_POSSIBLE, 2
    elif any(r.search(t) for r in _WEAK_RE):
        status, conf = ParkingStatus.LIKELY_INCLUDED, 2
    elif _ANY.search(t):
        status, conf = ParkingStatus.LIKELY_INCLUDED, 1
    else:
        status, conf = ParkingStatus.UNKNOWN, 0

    if structured_hint and status in (
        ParkingStatus.UNKNOWN,
        ParkingStatus.LIKELY_INCLUDED,
        ParkingStatus.AREA_POSSIBLE,
    ):
        status, conf = ParkingStatus.INCLUDED, max(conf, 2)
    return status, conf


# --- standalone parking-spot listings ----------------------------------------

_KIND_SUBTERAN = re.compile(r"subteran|demisol|subsol")
_KIND_GARAJ = re.compile(r"\bgaraj\b")
_KIND_EXTERIOR = re.compile(r"exterior|suprateran|aer liber|in curte|curte interioara")
_NUMBERED = re.compile(r"(?:loc(?:ul)?|parcare)\D{0,12}nr\.?\s*\d+|loc(?:ul)? \d+|numerotat")

# rent listings leaking into parking results (and vice versa)
PARKING_ONLY_TITLE = re.compile(
    r"(?:inchiriez|ofer|dau spre inchiriere)?\s*(?:loc(?:ul)? de parcare|loc parcare|"
    r"parcare subterana|garaj)\b"
)
APARTMENT_WORDS = re.compile(r"apartament|garsonier|\bcamere\b|\bcasa\b|\bvila\b|penthouse")


def classify_parking_spot(text: str) -> tuple[ParkingKind, bool]:
    """For a standalone parking listing: (kind, is_numbered)."""
    t = fold(" ".join((text or "").split()))
    if _KIND_SUBTERAN.search(t):
        kind = ParkingKind.SUBTERAN
    elif _KIND_GARAJ.search(t):
        kind = ParkingKind.GARAJ
    elif _KIND_EXTERIOR.search(t):
        kind = ParkingKind.EXTERIOR
    else:
        kind = ParkingKind.UNKNOWN
    return kind, bool(_NUMBERED.search(t))


def looks_like_parking_only(title: str) -> bool:
    """True when a title is a standalone parking/garage rental (not an apartment)."""
    t = fold(title or "")
    return bool(PARKING_ONLY_TITLE.search(t)) and not APARTMENT_WORDS.search(t)
