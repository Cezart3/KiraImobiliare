"""Price text -> EUR. Ported from the proven D:\\amin\\rent_scraper.py logic."""
import re

_NUM_CLEAN_RE = re.compile(r"[^\d,\.]")

# A price inside free card text. Romanian formats: "250", "1.500", "1 500".
# Anchored on purpose: thousands groups are exactly 3 digits and the number
# can't start with 0 — this stops badge counters glued in front of the price
# from being swallowed ("4 1 500 EUR" -> 1500 not 41500; "05 250 EUR" -> 250).
PRICE_TEXT_RE = re.compile(
    r"(?<![\d.,])([1-9]\d{0,2}(?:[ .]\d{3})+|[1-9]\d*)\s*(€|(?:eur(?:o)?|lei|ron)\b)",
    re.I,
)


def find_price_text(text: str) -> tuple[str, str] | None:
    """Extract (value, currency) from free text, or None."""
    m = PRICE_TEXT_RE.search(text or "")
    if not m:
        return None
    return m.group(1).strip(), m.group(2)


def _normalize_number(num: str) -> str:
    """Disambiguate separators: '1.500'/'1,000' are thousands (3-digit group),
    '906.29'/'906,29' are decimals (1-2 digits), '1.234.567' is thousands."""
    if "," in num and "." in num:
        # both present: the rightmost one is the decimal separator
        if num.rfind(",") > num.rfind("."):
            return num.replace(".", "").replace(",", ".")
        return num.replace(",", "")
    for sep in (",", "."):
        if sep in num:
            int_part, _, frac = num.rpartition(sep)
            if len(frac) == 3 and int_part:
                return num.replace(sep, "")          # thousands group(s)
            return int_part.replace(sep, "") + "." + frac  # decimal
    return num


def to_eur(raw: str | None, currency_hint: str = "", ron_per_eur: float = 5.0) -> float | None:
    """Parse a price string ('1.500 lei', '906.29 EUR', '450 €') into EUR."""
    if raw is None:
        return None
    s = str(raw).lower().replace("\xa0", " ")
    num = _NUM_CLEAN_RE.sub("", s)
    if not num:
        return None
    try:
        val = float(_normalize_number(num))
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
