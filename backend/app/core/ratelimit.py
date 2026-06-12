"""Tiny in-memory sliding-window rate limiter.

Per-process only — good enough for a single uvicorn worker. If we ever scale to
multiple workers, swap the backing store for Redis behind the same interface.
"""
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def allow(key: str, limit: int, window_s: float = 60.0) -> bool:
    now = time.monotonic()
    with _lock:
        dq = _hits[key]
        while dq and now - dq[0] > window_s:
            dq.popleft()
        if len(dq) >= limit:
            return False
        dq.append(now)
        return True


def enforce(request: Request, bucket: str, limit: int) -> None:
    """Raise 429 when the caller's IP exceeded `limit` calls/min on `bucket`."""
    ip = request.client.host if request.client else "?"
    if not allow(f"{bucket}:{ip}", limit):
        raise HTTPException(
            status_code=429, detail="Prea multe încercări. Reîncearcă peste un minut."
        )


def reset() -> None:
    """Test helper."""
    with _lock:
        _hits.clear()
