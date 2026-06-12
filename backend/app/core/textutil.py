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
