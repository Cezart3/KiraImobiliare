"""publi24.ro adapter — plain HTML cards (div.article-item).

Price is parsed from card text via regex (no structured price attrs).
Detail pages use ld+json (description + image contentUrl list, s3.publi24.ro).
"""
import json
import logging
import re
from collections.abc import Iterator
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.core.cities import CityConfig
from app.core.textutil import squash_ws
from app.scraping.base import RawListing, SiteScraper, register
from app.scraping.http import PoliteSession

log = logging.getLogger(__name__)

BASE = "https://www.publi24.ro"
_LDJSON_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
_PRICE_TXT_RE = re.compile(r"(\d[\d.\s]{1,9})\s*(€|eur|euro|lei|ron)", re.I)


class Publi24Scraper(SiteScraper):
    site = "publi24"
    supports_parking = False
    image_hosts = ("publi24.ro",)

    def __init__(self) -> None:
        self.http = PoliteSession()

    # ----- card -> RawListing ---------------------------------------------------

    def _to_raw(self, c) -> RawListing | None:
        a = c.find("a", href=True)
        if not a:
            return None
        url = urljoin(BASE, a["href"])
        card_text = squash_ws(c.get_text(" "))
        title = squash_ws(a.get_text(" "))[:120] or card_text[:80]

        price_value = ""
        price_currency = ""
        mp = _PRICE_TXT_RE.search(card_text)
        if mp:
            price_value = mp.group(1).strip()
            price_currency = mp.group(2)

        return RawListing(
            site=self.site,
            url=url,
            title=title,
            price_value=price_value,
            price_currency=price_currency,
            extra_text=card_text,
        )

    # ----- public API ---------------------------------------------------------

    def iter_rentals(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        # ?pagina= is ignored server-side (verified live: ~90% overlap, shuffled).
        # Scheduled re-runs surface the rotated listings instead. TODO: real param.
        max_pages = min(max_pages, 1)
        location = city.sites["publi24"]["location"]
        page = 1
        while page <= max_pages:
            url = f"{BASE}/anunturi/imobiliare/de-inchiriat/apartamente/{location}/"
            html = self.http.get_text(url, params={"pagina": page})
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.article-item")
            if not cards:
                break
            page_added = 0
            for c in cards:
                raw = self._to_raw(c)
                if raw:
                    yield raw
                    page_added += 1
            if page_added == 0:
                break
            page += 1

    def fetch_detail(self, item: RawListing) -> RawListing:
        html = self.http.get_text(item.url)
        if not html:
            return item

        m = _LDJSON_RE.search(html)
        if not m:
            return item
        try:
            d = json.loads(m.group(1), strict=False)
        except json.JSONDecodeError:
            return item

        desc = squash_ws(str(d.get("description") or ""))
        if len(desc) > len(item.description):
            item.description = desc

        images: list[str] = []
        for im in d.get("image") or []:
            u = im.get("contentUrl") if isinstance(im, dict) else None
            if u:
                images.append(u)
        if images:
            item.images = images[:8]

        return item


register(Publi24Scraper())
