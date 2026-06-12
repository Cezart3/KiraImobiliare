"""Street extraction from listing text (ported from proven D:\\amin\\parking_match.py)."""
import re

from app.core.textutil import fold

STREET_RE = re.compile(
    r"\b(?:str\.?|strada|b-?dul|bulevardul|bd\.?|calea|aleea|pia[țt]a|splaiul|"
    r"[șs]oseaua|[șs]os\.)\s+"
    r"([\wăâîșțĂÂÎȘȚ\.\-]+(?:\s+[\wăâîșțĂÂÎȘȚ0-9\.\-]+){0,2})",
    re.UNICODE | re.IGNORECASE,
)

# tokens that signal the street name ended (verbs / filler that leak into the match)
_STOPWORDS = {
    "inchiriez", "inchiriere", "salut", "se", "va", "oferim", "ofer", "compus",
    "este", "aproape", "nou", "pf", "proprietar", "recomandat", "pentru",
    "apartamentul", "caut", "coleg", "colega", "face", "in", "din", "zona",
    "cartier", "cartierul", "pret", "mobilat", "modern", "garsoniera",
    "apartament", "ap", "bloc", "etaj", "situat", "situata", "chiar", "foarte",
    "complet", "decomandat", "semidecomandat", "renovat", "lux", "superb",
}


def _clean_street(s: str, extra_stops: frozenset[str] = frozenset()) -> str:
    toks = s.strip().rstrip(".,;:- ").split()
    out: list[str] = []
    i = 0
    while i < len(toks):
        tok = toks[i]
        base = fold(tok.strip(".,;:"))
        if base in ("nr", "numar", "numarul"):
            # keep the house number itself ('str. Fabricii nr. 105' -> '... 105')
            nxt = toks[i + 1].strip(".,;:") if i + 1 < len(toks) else ""
            if nxt and nxt[0].isdigit():
                out.append(nxt)
                i += 2
                continue
            break
        if base in _STOPWORDS or base in extra_stops:
            break
        out.append(tok)
        i += 1
    return " ".join(out).rstrip(".,;:- ")


def extract_street(text: str, extra_stops: frozenset[str] = frozenset()) -> str:
    """Return 'strada X [nr]' style fragment, or ''. Keeps house numbers when present."""
    if not text:
        return ""
    t = " ".join(text.split())
    m = STREET_RE.search(t)
    if not m:
        return ""
    street = _clean_street(m.group(0), extra_stops)
    # a bare prefix like 'strada' with nothing left is useless
    if len(street.split()) < 2:
        return ""
    return street


def has_house_number(street: str) -> bool:
    return bool(re.search(r"\d", street or ""))
