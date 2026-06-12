from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import COOKIE_NAME, decode_session_token
from app.db.base import SessionLocal
from app.db.models import User


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    user_id = decode_session_token(token)
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_user(user: Annotated[User | None, Depends(get_current_user)]) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Autentificare necesară")
    return user
