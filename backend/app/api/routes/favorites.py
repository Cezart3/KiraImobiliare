"""Saved listings ("favorites") for logged-in users.

Anonymous users keep favorites in the browser (localStorage). When they log in,
the client POSTs the local ids to /favorites/sync to merge them server-side.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_user
from app.db.models import Favorite, Listing, User

router = APIRouter(prefix="/favorites", tags=["favorites"])


class IdsIn(BaseModel):
    ids: list[int]


def _valid_listing_ids(db: Session, ids: list[int]) -> set[int]:
    if not ids:
        return set()
    rows = db.scalars(select(Listing.id).where(Listing.id.in_(ids))).all()
    return set(rows)


@router.get("")
def list_favorites(
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    ids = db.scalars(
        select(Favorite.listing_id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    ).all()
    return {"ids": list(ids)}


@router.put("/{listing_id}")
def add_favorite(
    listing_id: int,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if not _valid_listing_ids(db, [listing_id]):
        return {"ok": False, "reason": "unknown-listing"}
    exists = db.scalar(
        select(Favorite).where(
            Favorite.user_id == user.id, Favorite.listing_id == listing_id
        )
    )
    if exists is None:
        db.add(Favorite(user_id=user.id, listing_id=listing_id))
        db.commit()
    return {"ok": True}


@router.delete("/{listing_id}")
def remove_favorite(
    listing_id: int,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    db.execute(
        delete(Favorite).where(
            Favorite.user_id == user.id, Favorite.listing_id == listing_id
        )
    )
    db.commit()
    return {"ok": True}


@router.post("/sync")
def sync_favorites(
    body: IdsIn,
    user: Annotated[User, Depends(require_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Merge a batch of client-side ids into the account (union, never delete).
    Returns the full merged list so the client can replace its local copy."""
    valid = _valid_listing_ids(db, body.ids[:500])  # cap to avoid abuse
    existing = set(
        db.scalars(select(Favorite.listing_id).where(Favorite.user_id == user.id)).all()
    )
    for lid in valid - existing:
        db.add(Favorite(user_id=user.id, listing_id=lid))
    if valid - existing:
        db.commit()
    merged = db.scalars(
        select(Favorite.listing_id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
    ).all()
    return {"ids": list(merged)}
