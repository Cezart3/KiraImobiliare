"""Scraper contracts. Each site adapter yields RawListing; the pipeline normalizes."""
from __future__ import annotations

import abc
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from app.core.cities import CityConfig


@dataclass(slots=True)
class RawListing:
    site: str
    url: str
    title: str = ""
    description: str = ""
    source_id: str | None = None
    price_value: str = ""        # raw price text/number as found on the site
    price_currency: str = ""     # currency hint as found (EUR / RON / lei ...)
    location_text: str = ""      # site-provided location string (city / district)
    images: list[str] = field(default_factory=list)
    rooms: int | None = None
    surface_m2: float | None = None
    floor: str | None = None
    posted_at: datetime | None = None
    parking_hint: bool = False   # structured parking/garage tag from the site
    extra_text: str = ""         # tags or any extra text fed to extractors


class SiteScraper(abc.ABC):
    """One adapter per source site. Adapters must be polite (delays, page caps)."""

    site: ClassVar[str]
    supports_parking: ClassVar[bool] = False
    # True when iter_parking uses a dedicated garage/parking category (results
    # trusted); False for keyword search (titles must look parking-only)
    parking_category_trusted: ClassVar[bool] = True
    # hosts allowed through the image proxy for this site
    image_hosts: ClassVar[tuple[str, ...]] = ()

    @abc.abstractmethod
    def iter_rentals(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        """Yield apartment rental listings for a city."""

    def iter_parking(self, city: CityConfig, max_pages: int) -> Iterator[RawListing]:
        """Yield standalone parking/garage rental listings (if supported)."""
        return iter(())

    def fetch_detail(self, item: RawListing) -> RawListing:
        """Optionally enrich an item with full description/images. Default no-op."""
        return item

    def is_enabled(self, city: CityConfig) -> bool:
        return self.site in city.sites


REGISTRY: dict[str, SiteScraper] = {}


def register(scraper: SiteScraper) -> SiteScraper:
    REGISTRY[scraper.site] = scraper
    return scraper


def allowed_image_hosts() -> frozenset[str]:
    hosts: set[str] = set()
    for s in REGISTRY.values():
        hosts.update(s.image_hosts)
    return frozenset(hosts)
