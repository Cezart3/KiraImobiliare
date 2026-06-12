"""Rooms / surface / floor extraction from Romanian listing text."""
import re

from app.core.textutil import fold

_GARSONIERA = re.compile(r"\bgarsonier")
_N_CAMERE = re.compile(r"\b(\d)\s*(?:camere|camera|cam\b)")
_WORD_CAMERE = [
    (re.compile(r"\bo camera\b"), 1),
    (re.compile(r"\bdoua camere\b"), 2),
    (re.compile(r"\btrei camere\b"), 3),
    (re.compile(r"\bpatru camere\b"), 4),
]
_SURFACE = re.compile(r"(\d{2,3}(?:[.,]\d)?)\s*(?:mp\b|m2\b|m²|metri patrati)")
_FLOOR = re.compile(r"etaj(?:ul)?\s*:?\s*(parter|demisol|mansarda|\d{1,2})")


def extract_rooms(text: str) -> int | None:
    t = fold(text)
    if _GARSONIERA.search(t):
        return 1
    m = _N_CAMERE.search(t)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 6:
            return n
    for rx, n in _WORD_CAMERE:
        if rx.search(t):
            return n
    return None


def extract_surface(text: str) -> float | None:
    m = _SURFACE.search(fold(text))
    if not m:
        return None
    val = float(m.group(1).replace(",", "."))
    return val if 10 <= val <= 400 else None


def extract_floor(text: str) -> str | None:
    m = _FLOOR.search(fold(text))
    return m.group(1) if m else None
