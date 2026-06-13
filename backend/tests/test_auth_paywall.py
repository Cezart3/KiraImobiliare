"""Auth (register/login/google/logout) + freemium paywall gating + billing state."""
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.routes import auth as auth_route
from app.core import ratelimit
from app.core.config import settings
from app.db.base import SessionLocal, init_db
from app.db.models import Listing, ParkingMatch, ParkingSpot, User, utcnow


def _seed_listings(n: int) -> None:
    with SessionLocal() as db:
        db.query(ParkingMatch).delete()
        db.query(Listing).delete()
        db.query(ParkingSpot).delete()
        db.query(User).delete()
        db.commit()
        for i in range(n):
            db.add(
                Listing(
                    site="storia",
                    url=f"https://pw/{i}",
                    title=f"Apartament {i}",
                    price_eur=300 + i,
                    rooms=2,
                    city_slug="cluj-napoca",
                    parking_status="unknown",
                    heating="unknown",
                    geo_precision="none",
                )
            )
        db.commit()


@pytest.fixture(scope="module")
def client():
    from app.main import app

    init_db()
    _seed_listings(12)
    ratelimit.reset()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def fresh_client():
    """Cookie-free client for anonymous requests."""
    from app.main import app

    return TestClient(app)


# ---------- auth ----------


def test_register_login_logout_me(client):
    r = client.post(
        "/api/auth/register", json={"email": "Ana@Example.com", "password": "parola123"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["authenticated"] is True
    assert body["email"] == "ana@example.com"  # normalized lowercase
    assert body["subscribed"] is False

    assert client.get("/api/auth/me").json()["authenticated"] is True

    # duplicate email
    r = client.post(
        "/api/auth/register", json={"email": "ana@example.com", "password": "parola123"}
    )
    assert r.status_code == 409

    # logout clears the session
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").json()["authenticated"] is False

    # login wrong password
    r = client.post(
        "/api/auth/login", json={"email": "ana@example.com", "password": "gresita99"}
    )
    assert r.status_code == 401

    # login OK
    r = client.post(
        "/api/auth/login", json={"email": "ana@example.com", "password": "parola123"}
    )
    assert r.status_code == 200
    assert client.get("/api/auth/me").json()["email"] == "ana@example.com"


def test_register_validation(client):
    assert (
        client.post(
            "/api/auth/register", json={"email": "not-an-email", "password": "parola123"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/auth/register", json={"email": "ok@example.com", "password": "scurt"}
        ).status_code
        == 422
    )
    # bcrypt hard limit: >72 bytes must be a clean 422, not a 500
    assert (
        client.post(
            "/api/auth/register", json={"email": "ok@example.com", "password": "x" * 80}
        ).status_code
        == 422
    )
    # oversized email -> 422 (column is 255; Postgres would error on insert)
    assert (
        client.post(
            "/api/auth/register",
            json={"email": "a" * 250 + "@example.com", "password": "parola123"},
        ).status_code
        == 422
    )
    # long password at LOGIN must not crash either (verify fails safe -> 401)
    assert (
        client.post(
            "/api/auth/login", json={"email": "ana@example.com", "password": "y" * 200}
        ).status_code
        == 401
    )


def test_google_login_creates_account_and_blocks_password(client, monkeypatch):
    monkeypatch.setattr(
        auth_route,
        "_verify_google_token",
        lambda cred: {"email": "G.User@Gmail.com", "email_verified": True},
    )
    r = client.post("/api/auth/google", json={"credential": "fake-jwt"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "g.user@gmail.com"

    # password login on a Google-only account is rejected with a clear message
    r = client.post(
        "/api/auth/login", json={"email": "g.user@gmail.com", "password": "oricare123"}
    )
    assert r.status_code == 401
    assert "Google" in r.json()["detail"]

    # second Google login reuses the account (no duplicate)
    r = client.post("/api/auth/google", json={"credential": "fake-jwt"})
    assert r.status_code == 200
    with SessionLocal() as db:
        assert db.query(User).filter(User.email == "g.user@gmail.com").count() == 1


def test_google_login_rejects_bad_token(client, monkeypatch):
    def boom(cred):
        raise ValueError("bad token")

    monkeypatch.setattr(auth_route, "_verify_google_token", boom)
    r = client.post("/api/auth/google", json={"credential": "junk"})
    assert r.status_code == 401


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "auth_rate_limit_per_min", 3)
    ratelimit.reset()
    payload = {"email": "rl@example.com", "password": "gresita99"}
    codes = [client.post("/api/auth/login", json=payload).status_code for _ in range(5)]
    assert codes[:3] == [401, 401, 401]
    assert codes[3] == 429 and codes[4] == 429
    ratelimit.reset()


# ---------- paywall gating ----------


def _listings(c: TestClient):
    r = c.get("/api/listings", params={"city": "cluj-napoca", "page_size": 60})
    assert r.status_code == 200, r.text
    return r.json()


def test_paywall_off_shows_everything(fresh_client):
    data = _listings(fresh_client)
    assert data["total"] == 12
    assert len(data["items"]) == 12
    assert data["locked"] is False
    assert data["visible_limit"] is None


def test_paywall_anonymous_capped_but_real_total(fresh_client, monkeypatch):
    monkeypatch.setattr(settings, "paywall_enabled", True)
    monkeypatch.setattr(settings, "free_listing_limit", 5)
    data = _listings(fresh_client)
    assert data["total"] == 12          # real count, always
    assert len(data["items"]) == 5      # capped
    assert data["locked"] is True
    assert data["visible_limit"] == 5
    assert data["pages"] == 1           # no pagination while locked

    # page=2 must not leak further results
    r = fresh_client.get(
        "/api/listings", params={"city": "cluj-napoca", "page": 2, "page_size": 60}
    )
    body = r.json()
    assert body["page"] == 1 and len(body["items"]) == 5


def test_paywall_free_user_capped(client, monkeypatch):
    monkeypatch.setattr(settings, "paywall_enabled", True)
    monkeypatch.setattr(settings, "free_listing_limit", 5)
    client.post(
        "/api/auth/login", json={"email": "ana@example.com", "password": "parola123"}
    )
    data = _listings(client)
    assert len(data["items"]) == 5 and data["locked"] is True


def test_paywall_subscriber_sees_all(client, monkeypatch):
    monkeypatch.setattr(settings, "paywall_enabled", True)
    monkeypatch.setattr(settings, "free_listing_limit", 5)
    with SessionLocal() as db:
        u = db.query(User).filter(User.email == "ana@example.com").one()
        u.sub_status = "active"
        u.sub_period_end = utcnow() + timedelta(days=30)  # paid access window
        db.commit()
    client.post(
        "/api/auth/login", json={"email": "ana@example.com", "password": "parola123"}
    )
    data = _listings(client)
    assert data["total"] == 12
    assert len(data["items"]) == 12
    assert data["locked"] is False


def test_delete_account(fresh_client):
    fresh_client.post(
        "/api/auth/register", json={"email": "del@example.com", "password": "parola123"}
    )
    r = fresh_client.post("/api/auth/delete-account")
    assert r.status_code == 200
    with SessionLocal() as db:
        assert db.query(User).filter(User.email == "del@example.com").count() == 0
    # session cookie is gone -> second delete is unauthorized
    assert fresh_client.post("/api/auth/delete-account").status_code == 401


# ---------- billing: one-time 30-day access ----------


def test_grant_access_one_time_and_renewal(client):
    from app.api.routes.billing import ACCESS_DAYS, grant_access

    with SessionLocal() as db:
        u = User(email=f"pay-{uuid.uuid4().hex[:8]}@example.com", password_hash="x")
        db.add(u)
        db.commit()

        # first payment: 30 days from now
        grant_access(db, u)
        db.refresh(u)
        assert u.sub_status == "active" and u.has_access() is True
        first_end = u.sub_period_end
        assert first_end is not None
        assert abs((first_end - utcnow()).days - ACCESS_DAYS) <= 1

        # renewal while still active: stacks another 30 days from current end
        grant_access(db, u)
        db.refresh(u)
        assert (u.sub_period_end - first_end).days == ACCESS_DAYS

        # expired access -> no access; buying again starts fresh from now
        u.sub_period_end = utcnow() - timedelta(days=1)
        db.commit()
        db.refresh(u)
        assert u.has_access() is False
        grant_access(db, u)
        db.refresh(u)
        assert u.has_access() is True
        assert abs((u.sub_period_end - utcnow()).days - ACCESS_DAYS) <= 1
