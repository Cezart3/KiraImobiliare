"""imobiliare.ro adapter — plain HTML cards (div[data-price]).

No parking category here (apartments only). Detail pages fetch description
(falls back to meta description) and roamcdn.net gallery images.

If the listing page is served behind a bot challenge (no cards found), this
adapter logs a warning and yields nothing rather than fighting anti-bot.
"""
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

BASE = "https://www.imobiliare.ro"
_ROAMCDN_RE = re.compile(r'https://i\.roamcdn\.net/prop/imo/gallery-main[^"\\\s]+\.jpg')


class ImobiliareScraper(SiteScraper):
    site = "imobiliare"
    supports_parking = False
    image_hosts = ("roamcdn.net",)

    def __init__(self) -> None:
        self.http = PoliteSession()

    # ----- card -> RawListing ---------------------------------------------------

    def _to_raw(self, c) -> RawListing | None:
        title = (c.get("data-name") or "").strip()
        a = c.find("a", href=True)
        if not a:
            return None
        url = urljoin(BASE, a["href"])

        price = c.get("data-price") or ""
        currency = c.get("data-bi-listing-currency") or ""
        card_text = squash_ws(c.get_text(" "))

        return RawListing(
            site=self.site,
            url=url,
            title=title,
            price_value=str(price),
            price_currency=str(currency),
            extra_text=card_text,
        )

    # ----- public API ---------------------------------------------------------

    def iter_rentals(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        # ?pagina= is ignored server-side (verified live: page2 set == page1 set).
        # TODO: find the real pagination mechanism (likely XHR on the new frontend).
        max_pages = min(max_pages, 1)
        location = city.sites["imobiliare"]["location"]
        page = 1
        while page <= max_pages:
            url = f"{BASE}/inchirieri-apartamente/{location}"
            html = self.http.get_text(url, params={"pagina": page})
            if not html:
                break
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div[data-price]")
            if not cards:
                if page == 1:
                    log.warning(
                        "imobiliare: no cards on page 1 (%s) — possible bot challenge", url
                    )
                break
            for c in cards:
                raw = self._to_raw(c)
                if raw:
                    yield raw
            page += 1

    def fetch_detail(self, item: RawListing) -> RawListing:
        html = self.http.get_text(item.url)
        if not html:
            return item
        soup = BeautifulSoup(html, "html.parser")

        desc = ""
        node = soup.find(attrs={"data-test": re.compile("descri", re.I)})
        if node:
            desc = squash_ws(node.get_text(" "))
        if not desc:
            m = soup.find("meta", attrs={"name": "description"})
            if m:
                desc = squash_ws(m.get("content", ""))
        if len(desc) > len(item.description):
            item.description = desc

        images = list(dict.fromkeys(_ROAMCDN_RE.findall(html)))[:8]
        if not images:
            images = self._own_gallery_images(soup)[:8]
        if images:
            item.images = images

        return item

    @staticmethod
    def _own_gallery_images(soup: BeautifulSoup) -> list[str]:
        """Newer detail pages render only thumbs client-side, intermixed with
        'recommended' cards. The listing's OWN photos are the roamcdn images
        NOT wrapped in an anchor pointing to another /oferta/ page."""
        out: list[str] = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if not src and img.get("srcset"):
                src = img["srcset"].split(",")[0].split()[0]
            if "roamcdn.net" not in src:
                continue
            anchor = img.find_parent("a", href=True)
            if anchor and "/oferta/" in anchor["href"]:
                continue  # thumbnail of a recommended listing
            out.append(src)
        # same photo can appear in several sizes -> dedupe by file name
        seen: set[str] = set()
        uniq: list[str] = []
        for u in out:
            name = u.rsplit("/", 1)[-1]
            if name in seen:
                continue
            seen.add(name)
            uniq.append(u)
        return uniq


register(ImobiliareScraper())
