"""lajumate.ro adapter — server-rendered __NEXT_DATA__ JSON. Apartment rentals.

Search pages embed `props.pageProps.adsServer` (list of ad objects for the
current page) and `props.pageProps.paginationServer` (currentPage/totalPages).
Each ad already carries its full image list, price/currency, city and listing
date — no detail-page fetch is needed (description is empty in list data, but
title covers it; fetch_detail is intentionally omitted).

No dedicated garage/parking rental category exists under "De inchiriat"
(only apartamente / garsoniere / case-vile / cazare-turism) -> parking
not supported.
"""
import json
import logging
import re
from collections.abc import Iterator
from contextlib import suppress
from datetime import datetime

from app.core.cities import CityConfig
from app.scraping.base import RawListing, SiteScraper, register
from app.scraping.http import PoliteSession

log = logging.getLogger(__name__)

BASE = "https://lajumate.ro"
# live-verified: ad pages live under /ad/<slug>-<id>; images are served through
# the opt-image resizer (static.lajumate.ro returns 404 for raw media paths)
IMG_BASE = "https://api-preprod.lajumate.ro/opt-image"
SEARCH_PATH = "/anunturi/imobiliare/apartamente-de-inchiriat/in"
_NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def _next_data(html_text: str) -> dict | None:
    m = _NEXT_RE.search(html_text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    with suppress(ValueError, TypeError):
        return datetime.fromisoformat(str(value).replace(" ", "T"))
    return None


class LajumateScraper(SiteScraper):
    site = "lajumate"
    supports_parking = False
    image_hosts = ("static.lajumate.ro", "lajumate.ro")

    def __init__(self) -> None:
        self.http = PoliteSession()

    # ----- search pages -------------------------------------------------------

    def iter_rentals(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        cfg = city.sites.get("lajumate") or {}
        location = cfg.get("location")
        if not location:
            log.warning("lajumate: missing location config for %s", city.slug)
            return

        page = 1
        while page <= max_pages:
            url = f"{BASE}{SEARCH_PATH}/{location}"
            params: dict = {}
            if page > 1:
                params["page"] = page
            html = self.http.get_text(url, params=params or None)
            if not html:
                break
            data = _next_data(html)
            if not data:
                log.warning("lajumate: no __NEXT_DATA__ on page %d (%s)", page, url)
                break
            try:
                pp = data["props"]["pageProps"]
            except (KeyError, TypeError):
                log.warning("lajumate: unexpected __NEXT_DATA__ shape on page %d (%s)", page, url)
                break

            ads = pp.get("adsServer")
            if not isinstance(ads, list) or not ads:
                if page == 1:
                    log.warning("lajumate: empty adsServer on page 1 (%s)", url)
                break

            for ad in ads:
                raw = self._to_raw(ad)
                if raw:
                    yield raw

            pag = pp.get("paginationServer") or {}
            total_pages = pag.get("totalPages") or 1
            if page >= total_pages:
                break
            page += 1

    def _to_raw(self, ad: dict) -> RawListing | None:
        ad_id = ad.get("id")
        slug = ad.get("slug") or ""
        title = (ad.get("title") or "").strip()
        if not ad_id or not title:
            log.warning("lajumate: skipping ad with missing id/title: %s", ad.get("id"))
            return None

        url = f"{BASE}/ad/{slug}-{ad_id}" if slug else f"{BASE}/ad/{ad_id}"

        description = (ad.get("description") or "").strip()

        price_value = str(ad.get("price") or "")
        price_currency = str(ad.get("currency") or "")

        location_text = ""
        city_info = ad.get("city") or {}
        with suppress(AttributeError, TypeError):
            city_name = city_info.get("name") or ""
            county_name = (city_info.get("county") or {}).get("name") or ""
            location_text = ", ".join(p for p in (city_name, county_name) if p)

        images: list[str] = []
        for im in ad.get("images") or []:
            if not isinstance(im, dict):
                continue
            path = im.get("path")
            if path:
                images.append(f"{IMG_BASE}/{path.lstrip('/')}?w=800")
        if not images:
            log.warning("lajumate: ad %s has no images", ad_id)

        return RawListing(
            site=self.site,
            url=url,
            source_id=str(ad_id),
            title=title,
            description=description,
            price_value=price_value,
            price_currency=price_currency,
            location_text=location_text,
            images=images[:8],
            posted_at=_parse_dt(ad.get("listed_at")),
            extra_text=title,
        )


register(LajumateScraper())
