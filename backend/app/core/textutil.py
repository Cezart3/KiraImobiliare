"""Text helpers shared by extractors and pipeline."""
import html as html_lib
import re
import unicodedata

_WS_RE = re.compile(r"\s+")
_BR_RE = re.compile(r"<br\s*/?>", re.I)
_TAG_RE = re.compile(r"<[^>]+>")


def squash_ws(s: str | None) -> str:
    return _WS_RE.sub(" ", s or "").strip()


def strip_html(s: str | None) -> str:
    if not s:
        return ""
    s = _BR_RE.sub(" ", s)
    s = _TAG_RE.sub(" ", s)
    return squash_ws(html_lib.unescape(s))


def fold(s: str | None) -> str:
    """Lowercase + strip diacritics (ă→a, ș→s, ț→t...) for robust RO matching."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# --- personal-data redaction --------------------------------------------------
# We only need the rental facts + a link back to the source; we do NOT want to
# store contact details. Strip RO phone numbers + emails from any text we keep.
# (The user still sees the real contact on the original ad we link to.)
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?40|0)\s?7\d(?:[\s.\-]?\d){7}(?!\d)"  # RO mobile: 07xx xxx xxx / +407...
)
_PHONE_LANDLINE_RE = re.compile(
    r"(?<!\d)(?:\+?40|0)\s?(?:2|3)\d(?:[\s.\-]?\d){7}(?!\d)"  # RO landline 02/03...
)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_REDACT = "[contact pe site]"


def redact_personal(s: str | None) -> str:
    """Remove phone numbers + emails from listing text (GDPR data minimisation)."""
    if not s:
        return ""
    s = _PHONE_RE.sub(_REDACT, s)
    s = _PHONE_LANDLINE_RE.sub(_REDACT, s)
    s = _EMAIL_RE.sub(_REDACT, s)
    return s
