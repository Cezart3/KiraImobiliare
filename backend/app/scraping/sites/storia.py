"""storia.ro adapter — server-rendered __NEXT_DATA__ JSON. Rentals + garages.

Reference adapter: other site adapters follow this structure.
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

BASE = "https://www.storia.ro"
_NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
_TAG_PARKING = re.compile(r"GARAGE|PARKING", re.I)
_ROOMS_WORDS = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5, "SIX": 6}


def _next_data(html_text: str) -> dict | None:
    m = _NEXT_RE.search(html_text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _parse_rooms(value) -> int | None:
    if isinstance(value, int):
        return value if 1 <= value <= 6 else None
    if isinstance(value, str):
        return _ROOMS_WORDS.get(value.upper())
    return None


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    with suppress(ValueError, TypeError):
        return datetime.fromisoformat(str(value).replace(" ", "T").replace("Z", "+00:00"))
    return None


class StoriaScraper(SiteScraper):
    site = "storia"
    supports_parking = True
    image_hosts = ("olxcdn.com", "storia.ro")

    def __init__(self) -> None:
        self.http = PoliteSession()

    # ----- search pages -------------------------------------------------------

    def _iter_search(
        self, city: CityConfig, kind_path: str, max_pages: int
    ) -> Iterator[RawListing]:
        location = city.sites["storia"]["location"]
        page = 1
        while page <= max_pages:
            url = f"{BASE}/ro/rezultate/inchiriere/{kind_path}/{location}"
            params = {"page": page, "by": "LATEST", "direction": "DESC"}
            html = self.http.get_text(url, params=params)
            if not html:
                break
            data = _next_data(html)
            if not data:
                log.warning("storia: no __NEXT_DATA__ on page %d (%s)", page, kind_path)
                break
            try:
                sa = data["props"]["pageProps"]["data"]["searchAds"]
            except (KeyError, TypeError):
                break
            items = sa.get("items") or []
            if not items:
                break
            for it in items:
                raw = self._to_raw(it)
                if raw:
                    yield raw
            total_pages = (sa.get("pagination") or {}).get("totalPages") or 1
            if page >= total_pages:
                break
            page += 1

    def _to_raw(self, it: dict) -> RawListing | None:
        slug = it.get("slug") or ""
        href = it.get("href") or ""
        if slug:
            url = f"{BASE}/ro/oferta/{slug}"
        elif href:
            url = BASE + href.replace("[lang]", "ro")
        else:
            return None

        tp = it.get("totalPrice") or {}
        location_parts: list[str] = []
        with suppress(AttributeError, TypeError):
            addr = (it.get("location") or {}).get("address") or {}
            for key in ("street", "district", "city"):
                name = (addr.get(key) or {}).get("name")
                if name:
                    location_parts.append(str(name))

        images: list[str] = []
        for im in it.get("images") or []:
            if isinstance(im, dict):
                u = im.get("large") or im.get("medium") or im.get("small")
                if u:
                    images.append(u)

        tag_text = " ".join(
            t.get("value", "") for t in (it.get("tags") or []) if isinstance(t, dict)
        )

        return RawListing(
            site=self.site,
            url=url,
            source_id=str(it.get("id") or "") or None,
            title=(it.get("title") or "").strip(),
            description=strip_html(it.get("shortDescription") or ""),
            price_value=str(tp.get("value", "")),
            price_currency=str(tp.get("currency", "")),
            location_text=", ".join(location_parts),
            images=images[:8],
            rooms=_parse_rooms(it.get("roomsNumber")),
            surface_m2=it.get("areaInSquareMeters")
            if isinstance(it.get("areaInSquareMeters"), int | float)
            else None,
            posted_at=_parse_dt(it.get("dateCreatedFirst") or it.get("dateCreated")),
            parking_hint=bool(_TAG_PARKING.search(tag_text)),
            extra_text=tag_text,
        )

    # ----- public API ---------------------------------------------------------

    def iter_rentals(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        yield from self._iter_search(city, "apartament", max_pages)

    def iter_parking(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        yield from self._iter_search(city, "garaj", max_pages)

    def fetch_detail(self, item: RawListing) -> RawListing:
        html = self.http.get_text(item.url)
        if not html:
            return item
        data = _next_data(html)
        if not data:
            return item
        try:
            ad = data["props"]["pageProps"]["ad"]
        except (KeyError, TypeError):
            return item

        desc = strip_html(str(ad.get("description") or ""))
        if len(desc) > len(item.description):
            item.description = desc

        images: list[str] = []
        for im in ad.get("images") or []:
            if isinstance(im, dict):
                u = im.get("large") or im.get("medium")
                if u:
                    images.append(u)
        if images:
            item.images = images[:8]

        # structured characteristics (heating, floor...) -> feed to extractors as text
        extras: list[str] = []
        for ch in ad.get("characteristics") or []:
            if isinstance(ch, dict):
                lv = ch.get("localizedValue") or ch.get("value")
                lk = ch.get("localizedKey") or ch.get("key")
                if lk and lv:
                    extras.append(f"{lk}: {lv}")
        with suppress(AttributeError, TypeError):
            street = (((ad.get("location") or {}).get("address") or {}).get("street") or {}).get(
                "name"
            )
            if street:
                extras.append(f"strada {street}")
        if extras:
            item.extra_text = (item.extra_text + " | " + "; ".join(extras)).strip(" |")
        return item


register(StoriaScraper())
