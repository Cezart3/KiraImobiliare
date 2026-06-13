from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParkingSpotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site: str
    url: str
    title: str
    price_eur: float | None
    kind: str
    is_numbered: bool
    zone_slug: str | None
    address_extracted: str
    lat: float | None
    lon: float | None


class ParkingMatchOut(BaseModel):
    parking: ParkingSpotOut
    distance_m: int
    walk_min: float
    is_approx: bool
    maps_url: str


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site: str
    url: str
    title: str
    snippet: str = ""
    price_eur: float | None
    price_negotiable: bool = False
    rooms: int | None
    surface_m2: float | None
    floor: str | None
    city_slug: str
    zone_slug: str | None
    in_nearby_town: bool
    town_slug: str | None
    address_extracted: str = ""
    parking_status: str
    parking_confidence: int
    heating: str
    images: list[str] = []
    lat: float | None
    lon: float | None
    geo_precision: str
    posted_at: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    dedup_group: str | None
    parking_match_count: int = 0
    best_parking: ParkingMatchOut | None = None


class ListingDetailOut(ListingOut):
    description: str = ""
    parking_matches: list[ParkingMatchOut] = []


class ListingPage(BaseModel):
    items: list[ListingOut]
    total: int          # always the REAL count, also for free users
    page: int
    page_size: int
    pages: int
    locked: bool = False           # true when results were cut by the paywall
    visible_limit: int | None = None
