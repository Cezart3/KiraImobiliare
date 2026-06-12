"""Global per-IP rate-limit middleware."""
from fastapi.testclient import TestClient

from app.core import ratelimit
from app.core.config import settings


def test_global_rate_limit_blocks_floods(monkeypatch):
    from app.main import app

    monkeypatch.setattr(settings, "global_rate_limit_per_min", 5)
    ratelimit.reset()
    try:
        with TestClient(app) as client:
            codes = [client.get("/api/health").status_code for _ in range(8)]
        assert codes[:5] == [200] * 5
        assert codes[5:] == [429] * 3
    finally:
        ratelimit.reset()


def test_global_rate_limit_off_when_zero(monkeypatch):
    from app.main import app

    monkeypatch.setattr(settings, "global_rate_limit_per_min", 0)
    ratelimit.reset()
    with TestClient(app) as client:
        codes = [client.get("/api/health").status_code for _ in range(20)]
    assert set(codes) == {200}
