"""Password hashing (bcrypt) + session tokens (JWT in an httpOnly cookie)."""
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

ALGO = "HS256"
COOKIE_NAME = "rs_session"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def create_session_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(UTC) + timedelta(days=settings.session_days),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGO)


def decode_session_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGO])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
