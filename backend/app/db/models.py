"""ORM models. Datetimes are stored as naive UTC (SQLite-safe comparisons)."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    """Naive UTC now — consistent across SQLite/Postgres string comparison."""
    return datetime.now(UTC).replace(tzinfo=None)


class ParkingStatus(StrEnum):
    INCLUDED = "included"               # parking/garage part of the rental
    LIKELY_INCLUDED = "likely_included"  # parking mentioned, not explicit
    AREA_POSSIBLE = "area_possible"     # 'posibilitate parcare', street/free parking nearby
    NONE = "none"                       # explicitly without parking
    UNKNOWN = "unknown"


class Heating(StrEnum):
    CENTRALA_PROPRIE = "centrala_proprie"
    TERMOFICARE = "termoficare"         # district / building-level heating
    UNKNOWN = "unknown"


class GeoPrecision(StrEnum):
    EXACT = "exact"     # street + number
    STREET = "street"   # street-level geocode
    ZONE = "zone"       # neighbourhood centroid
    CITY = "city"       # city-centre fallback
    NONE = "none"


class ParkingKind(StrEnum):
    SUBTERAN = "subteran"
    GARAJ = "garaj"
    EXTERIOR = "exterior"
    UNKNOWN = "unknown"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    site: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[str | None] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(700), unique=True)
    title: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")

    price_eur: Mapped[float | None] = mapped_column(Float, index=True)
    price_raw: Mapped[str] = mapped_column(String(64), default="")
    rooms: Mapped[int | None] = mapped_column(Integer, index=True)
    surface_m2: Mapped[float | None] = mapped_column(Float)
    floor: Mapped[str | None] = mapped_column(String(32))

    city_slug: Mapped[str] = mapped_column(String(32), index=True)
    zone_slug: Mapped[str | None] = mapped_column(String(48), index=True)
    in_nearby_town: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    town_slug: Mapped[str | None] = mapped_column(String(48))
    location_raw: Mapped[str] = mapped_column(String(255), default="")
    address_extracted: Mapped[str] = mapped_column(String(255), default="")
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    geo_precision: Mapped[str] = mapped_column(String(12), default=GeoPrecision.NONE.value)

    parking_status: Mapped[str] = mapped_column(
        String(20), default=ParkingStatus.UNKNOWN.value, index=True
    )
    parking_confidence: Mapped[int] = mapped_column(Integer, default=0)
    heating: Mapped[str] = mapped_column(String(20), default=Heating.UNKNOWN.value, index=True)

    images: Mapped[list] = mapped_column(JSON, default=list)

    posted_at: Mapped[datetime | None] = mapped_column(DateTime)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    dedup_group: Mapped[str | None] = mapped_column(String(64), index=True)

    parking_matches: Mapped[list[ParkingMatch]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_listings_city_price", "city_slug", "price_eur"),)


class ParkingSpot(Base):
    __tablename__ = "parking_spots"

    id: Mapped[int] = mapped_column(primary_key=True)
    site: Mapped[str] = mapped_column(String(32), index=True)
    url: Mapped[str] = mapped_column(String(700), unique=True)
    title: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    price_eur: Mapped[float | None] = mapped_column(Float, index=True)

    city_slug: Mapped[str] = mapped_column(String(32), index=True)
    zone_slug: Mapped[str | None] = mapped_column(String(48), index=True)
    address_extracted: Mapped[str] = mapped_column(String(255), default="")
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    geo_precision: Mapped[str] = mapped_column(String(12), default=GeoPrecision.NONE.value)

    kind: Mapped[str] = mapped_column(String(16), default=ParkingKind.UNKNOWN.value, index=True)
    is_numbered: Mapped[bool] = mapped_column(Boolean, default=False)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    matches: Mapped[list[ParkingMatch]] = relationship(
        back_populates="parking", cascade="all, delete-orphan"
    )


class ParkingMatch(Base):
    __tablename__ = "parking_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    parking_id: Mapped[int] = mapped_column(
        ForeignKey("parking_spots.id", ondelete="CASCADE"), index=True
    )
    distance_m: Mapped[int] = mapped_column(Integer)
    walk_min: Mapped[float] = mapped_column(Float)
    is_approx: Mapped[bool] = mapped_column(Boolean, default=False)

    listing: Mapped[Listing] = relationship(back_populates="parking_matches")
    parking: Mapped[ParkingSpot] = relationship(back_populates="matches")

    __table_args__ = (UniqueConstraint("listing_id", "parking_id", name="uq_match_pair"),)


class GeoCache(Base):
    __tablename__ = "geo_cache"

    query: Mapped[str] = mapped_column(String(255), primary_key=True)
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    found: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    stripe_customer_id: Mapped[str | None] = mapped_column(String(64), index=True)
    # none | active | past_due | canceled — access lasts until sub_period_end
    sub_status: Mapped[str] = mapped_column(String(16), default="none")
    sub_period_end: Mapped[datetime | None] = mapped_column(DateTime)

    def has_access(self) -> bool:
        if self.sub_status == "active":
            return True
        return self.sub_period_end is not None and self.sub_period_end > utcnow()


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    site: Mapped[str] = mapped_column(String(32), index=True)
    city_slug: Mapped[str] = mapped_column(String(32), index=True)
    kind: Mapped[str] = mapped_column(String(12), default="rent")  # rent | parking
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(12), default="running")  # running|ok|error
    items_found: Mapped[int] = mapped_column(Integer, default=0)
    items_upserted: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
