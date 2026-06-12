from datetime import datetime

from pydantic import BaseModel


class PlaceOut(BaseModel):
    slug: str
    name: str


class CityOut(BaseModel):
    slug: str
    name: str
    zones: list[PlaceOut]
    nearby_towns: list[PlaceOut]
    sites: list[str]


class SiteRunOut(BaseModel):
    site: str
    kind: str
    status: str
    finished_at: datetime | None
    items_found: int
    items_upserted: int


class CityStatsOut(BaseModel):
    city_slug: str
    active_listings: int
    active_parking: int
    last_runs: list[SiteRunOut]
