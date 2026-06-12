"""capitalimobiliare.ro adapter — Cluj-only rental agency, plain HTML.

Card layout: anchors to /proprietate/<slug>/ wrapped a few parents up in a
listing-card container; price text like "750€/lună" embedded in the card text.
Pagination: /inchiriere-apartamente/page/N/.

Enabled only for cities with "capital" in city.sites (Cluj-Napoca).
"""
import logging
import re
from collections.abc import Iterator

from bs4 import BeautifulSoup

from app.core.cities import CityConfig
from app.core.textutil import squash_ws
from app.scraping.base import RawListing, SiteScraper, register
from app.scraping.http import PoliteSession

log = logging.getLogger(__name__)

BASE = "https://capitalimobiliare.ro"
LIST_URL = f"{BASE}/inchiriere-apartamente/"
_CAP_PRICE_RE = re.compile(r"([\d.,]+)\s*€\s*/?\s*lun", re.I)
_TITLE_STRIP_RE = re.compile(r"Comision 0%|/?lun[ăa]|\d[\d.,]*\s*€", re.I)
_PROPERTY_IMG_RE = re.compile(
    r"https://capitalimobiliare\.ro/wp-content/uploads/[^\"'\s]+property-image[^\"'\s]+\.(?:jpg|jpeg|webp)"
)
_OG_IMAGE_RE = re.compile(r'og:image" content="([^"]+)')


class CapitalScraper(SiteScraper):
    site = "capital"
    supports_parking = False
    image_hosts = ("capitalimobiliare.ro",)

    def __init__(self) -> None:
        self.http = PoliteSession()

    # ----- card -> RawListing ---------------------------------------------------

    def _to_raw(self, href: str, txt: str) -> RawListing | None:
        mp = _CAP_PRICE_RE.search(txt)
        if not mp:
            return None
        # Capital format: "1,000€" = 1000 (comma=thousands, no decimals)
        price_raw = mp.group(1).replace(".", "").replace(",", "").strip()
        if not price_raw.isdigit():
            return None

        title = squash_ws(_TITLE_STRIP_RE.sub(" ", txt))[:90]

        return RawListing(
            site=self.site,
            url=href,
            title=title,
            price_value=price_raw,
            price_currency="EUR",
            location_text="Cluj-Napoca",
            extra_text=txt[:200],
        )

    # ----- public API ---------------------------------------------------------

    def is_enabled(self, city: CityConfig) -> bool:
        return "capital" in city.sites

    def iter_rentals(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        seen: set[str] = set()
        for page in range(1, max_pages + 1):
            url = LIST_URL if page == 1 else f"{LIST_URL}page/{page}/"
            html = self.http.get_text(url)
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            anchors = soup.select('a[href*="/proprietate/"]')
            cards: dict[str, str] = {}
            for a in anchors:
                href = a["href"].split("#")[0]
                if href in cards:
                    continue
                card = a
                for _ in range(6):
                    if card.parent:
                        card = card.parent
                cards[href] = squash_ws(card.get_text(" "))
            if not cards:
                if page == 1:
                    log.warning("capital: no /proprietate/ cards found on page 1 (%s)", url)
                break
            page_added = 0
            for href, txt in cards.items():
                if href in seen:
                    continue
                seen.add(href)
                raw = self._to_raw(href, txt)
                if raw:
                    yield raw
                    page_added += 1
            if page_added == 0:
                break

    def fetch_detail(self, item: RawListing) -> RawListing:
        html = self.http.get_text(item.url)
        if not html:
            return item
        soup = BeautifulSoup(html, "html.parser")

        node = soup.select_one("[class*=descri]")
        if node:
            desc = squash_ws(node.get_text(" "))
            # drop the leading "Descriere" heading text
            desc = re.sub(r"^Descriere\s*", "", desc, flags=re.I)
            if len(desc) > len(item.description):
                item.description = desc

        images = list(dict.fromkeys(_PROPERTY_IMG_RE.findall(html)))[:8]
        if not images:
            m = _OG_IMAGE_RE.search(html)
            if m:
                images = [m.group(1)]
        if images:
            item.images = images

        return item


register(CapitalScraper())
