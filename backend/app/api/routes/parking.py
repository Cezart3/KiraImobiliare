from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.db.models import ParkingSpot, utcnow
from app.schemas.listing import ParkingSpotOut

router = APIRouter(tags=["parking"])


@router.get("/parking", response_model=list[ParkingSpotOut])
def list_parking(
    city: str,
    db: Annotated[Session, Depends(get_db)],
    zones: Annotated[list[str] | None, Query()] = None,
    kind: Annotated[list[str] | None, Query()] = None,
    price_max: float | None = None,
    limit: Annotated[int, Query(ge=1, le=300)] = 200,
):
    cutoff = utcnow() - timedelta(days=settings.listing_active_days)
    conds = [ParkingSpot.city_slug == city, ParkingSpot.last_seen_at >= cutoff]
    if zones:
        conds.append(ParkingSpot.zone_slug.in_(zones))
    if kind:
        conds.append(ParkingSpot.kind.in_(kind))
    if price_max is not None:
        conds.append(ParkingSpot.price_eur <= price_max)
    rows = db.scalars(
        select(ParkingSpot)
        .where(*conds)
        .order_by(ParkingSpot.price_eur.asc().nulls_last())
        .limit(limit)
    ).all()
    return rows
