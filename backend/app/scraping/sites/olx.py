"""olx.ro adapter — list pages embed full ad data in window.__PRERENDERED_STATE__.

Rentals + standalone parking (keyword search). Detail pages use the same
PRERENDERED_STATE structure under ad.ad.
"""
import json
import logging
import re
from collections.abc import Iterator
from contextlib import suppress
from datetime import datetime

from app.core.cities import CityConfig
from app.core.textutil import strip_html
from app.scraping.base import RawListing, SiteScraper, register
from app.scraping.http import PoliteSession

log = logging.getLogger(__name__)

BASE = "https://www.olx.ro"
_STATE_MARKER = "window.__PRERENDERED_STATE__"
_IMG_SIZE_RE = re.compile(r";s=\d+x\d+")

# Generic parking/garage search queries (1 page each, deduped by url)
_PARKING_QUERIES = (
    "inchiriez-loc-parcare",
    "loc-de-parcare",
    "garaj-de-inchiriat",
    "parcare-subterana",
    "inchiriez-garaj",
    "parcare-de-inchiriat",
    "chirie-parcare",
    "loc-parcare",
)


def _extract_js_string(html_text: str, var_marker: str) -> str | None:
    """Extract the quoted JS string assigned to a var, return decoded Python str."""
    idx = html_text.find(var_marker)
    if idx < 0:
        return None
    i = idx + len(var_marker)
    while i < len(html_text) and html_text[i] in " \t=":
        i += 1
    if i >= len(html_text) or html_text[i] != '"':
        return None
    i += 1
    buf = []
    while i < len(html_text):
        c = html_text[i]
        if c == "\\":
            buf.append(html_text[i:i + 2])
            i += 2
            continue
        if c == '"':
            break
        buf.append(c)
        i += 1
    try:
        return json.loads('"' + "".join(buf) + '"')
    except json.JSONDecodeError:
        return None


def _prerendered_state(html_text: str) -> dict | None:
    raw = _extract_js_string(html_text, _STATE_MARKER)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    with suppress(ValueError, TypeError):
        return datetime.fromisoformat(str(value).replace(" ", "T").replace("Z", "+00:00"))
    return None


def _photo_urls(photos: list) -> list[str]:
    out: list[str] = []
    for p in photos or []:
        link = p if isinstance(p, str) else (p.get("link") or "") if isinstance(p, dict) else ""
        if not link:
            continue
        out.append(_IMG_SIZE_RE.sub(";s=800x600", link))
    return out


class OlxScraper(SiteScraper):
    site = "olx"
    supports_parking = True
    parking_category_trusted = False
    image_hosts = ("olxcdn.com",)

    def __init__(self) -> None:
        self.http = PoliteSession()

    # ----- ad -> RawListing -----------------------------------------------------

    def _to_raw(self, a: dict) -> RawListing | None:
        if a.get("isJob"):
            return None
        url = a.get("url") or ""
        if not url:
            return None

        rp = ((a.get("price") or {}).get("regularPrice")) or {}

        loc = a.get("location") or {}
        location_parts: list[str] = []
        with suppress(AttributeError, TypeError):
            if loc.get("cityName"):
                location_parts.append(str(loc["cityName"]))
            if loc.get("districtName"):
                location_parts.append(str(loc["districtName"]))

        return RawListing(
            site=self.site,
            url=url,
            source_id=str(a.get("id") or "") or None,
            title=(a.get("title") or "").strip(),
            description=strip_html(a.get("description") or ""),
            price_value=str(rp.get("value", "")),
            price_currency=str(rp.get("currencyCode", "")),
            location_text=", ".join(location_parts),
            images=_photo_urls(a.get("photos"))[:8],
            posted_at=_parse_dt(a.get("createdTime") or a.get("lastRefreshTime")),
        )

    # ----- search pages -----------------------------------------------------------

    def _iter_search(self, url_tmpl: str, max_pages: int) -> Iterator[RawListing]:
        page = 1
        while page <= max_pages:
            html = self.http.get_text(url_tmpl, params={"page": page})
            if not html:
                break
            state = _prerendered_state(html)
            if not state:
                log.warning("olx: no __PRERENDERED_STATE__ on page %d (%s)", page, url_tmpl)
                break
            try:
                listing = state["listing"]["listing"]
            except (KeyError, TypeError):
                break
            ads = listing.get("ads") or []
            if not ads:
                break
            for a in ads:
                raw = self._to_raw(a)
                if raw:
                    yield raw
            total_pages = listing.get("totalPages") or 1
            if page >= total_pages:
                break
            page += 1

    # ----- public API ---------------------------------------------------------

    def iter_rentals(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        location = city.sites["olx"]["location"]
        url = f"{BASE}/imobiliare/apartamente-garsoniere-de-inchiriat/{location}/"
        yield from self._iter_search(url, max_pages)

    def iter_parking(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        location = city.sites["olx"]["location"]
        seen: set[str] = set()
        for q in _PARKING_QUERIES:
            url = f"{BASE}/imobiliare/{location}/q-{q}/"
            for raw in self._iter_search(url, 1):
                if raw.url in seen:
                    continue
                seen.add(raw.url)
                yield raw

    def fetch_detail(self, item: RawListing) -> RawListing:
        html = self.http.get_text(item.url)
        if not html:
            return item
        state = _prerendered_state(html)
        if not state:
            return item
        try:
            ad = state["ad"]["ad"]
        except (KeyError, TypeError):
            return item

        desc = strip_html(str(ad.get("description") or ""))
        if len(desc) > len(item.description):
            item.description = desc

        images = _photo_urls(ad.get("photos"))
        if images:
            item.images = images[:8]

        return item


register(OlxScraper())
