"""Price text -> EUR. Ported from the proven D:\\amin\\rent_scraper.py logic."""
import re

_NUM_CLEAN_RE = re.compile(r"[^\d,\.]")


def to_eur(raw: str | None, currency_hint: str = "", ron_per_eur: float = 5.0) -> float | None:
    """Parse a price string ('1.500 lei', '450 €', '450', 'EUR') into EUR.

    RO convention: '.' thousands separator, ',' decimal separator.
    """
    if raw is None:
        return None
    s = str(raw).lower().replace("\xa0", " ")
    num = _NUM_CLEAN_RE.sub("", s)
    if not num:
        return None
    num = num.replace(".", "").replace(",", ".")
    try:
        val = float(num)
    except ValueError:
        return None

    is_ron = ("lei" in s or "ron" in s) and "eur" not in s and "€" not in s
    hint = (currency_hint or "").upper()
    if hint in ("RON", "LEI"):
        is_ron = True
    if hint == "EUR" or "€" in s or "eur" in s:
        is_ron = False
    if is_ron:
        val = val / ron_per_eur
    return round(val, 1)
