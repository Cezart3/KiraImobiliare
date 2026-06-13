"""Favorites CRUD + sync, and distance-from-origin annotation."""
import pytest
from fastapi.testclient import TestClient

from app.db.base import SessionLocal, init_db
from app.db.models import Favorite, Listing, User


def _seed() -> list[int]:
    with SessionLocal() as db:
        db.query(Favorite).delete()
        db.query(Listing).delete()
        db.query(User).filter(User.email == "fav@example.com").delete()
        db.commit()
        ids = []
        for i in range(3):
            listing = Listing(
                site="storia",
                url=f"https://fav/{i}",
                title=f"Ap {i}",
                price_eur=300 + i,
                rooms=2,
                city_slug="cluj-napoca",
                parking_status="unknown",
                heating="unknown",
                geo_precision="zone",
                lat=46.77 + i * 0.01,
                lon=23.59,
            )
            db.add(listing)
            db.flush()
            ids.append(listing.id)
        db.commit()
        return ids


@pytest.fixture(scope="module")
def client():
    from app.main import app

    init_db()
    ids = _seed()
    with TestClient(app) as c:
        c._listing_ids = ids  # type: ignore[attr-defined]
        yield c


def _login(client) -> None:
    client.post(
        "/api/auth/register",
        json={"email": "fav@example.com", "password": "parola1234"},
    )


def test_favorites_require_auth(client):
    fresh = TestClient(client.app)
    assert fresh.get("/api/favorites").status_code == 401


def test_favorites_crud(client):
    ids = client._listing_ids  # type: ignore[attr-defined]
    _login(client)
    assert client.get("/api/favorites").json()["ids"] == []

    client.put(f"/api/favorites/{ids[0]}")
    client.put(f"/api/favorites/{ids[1]}")
    saved = set(client.get("/api/favorites").json()["ids"])
    assert saved == {ids[0], ids[1]}

    # idempotent add
    client.put(f"/api/favorites/{ids[0]}")
    assert len(client.get("/api/favorites").json()["ids"]) == 2

    # unknown listing -> not added
    r = client.put("/api/favorites/99999")
    assert r.json()["ok"] is False

    client.delete(f"/api/favorites/{ids[0]}")
    assert client.get("/api/favorites").json()["ids"] == [ids[1]]


def test_favorites_sync_merges(client):
    ids = client._listing_ids  # type: ignore[attr-defined]
    _login(client)
    # current server state from previous test: {ids[1]}; sync ids[2] + junk
    merged = client.post(
        "/api/favorites/sync", json={"ids": [ids[2], 99999]}
    ).json()["ids"]
    assert ids[2] in merged and ids[1] in merged and 99999 not in merged


def test_listings_by_ids(client):
    ids = client._listing_ids  # type: ignore[attr-defined]
    r = client.get("/api/listings-by-ids", params=[("ids", ids[2]), ("ids", ids[0])])
    assert r.status_code == 200
    body = r.json()
    # returns requested listings, preserving caller order when no `near`
    assert [item["id"] for item in body] == [ids[2], ids[0]]
    # empty ids -> empty list, unknown ids skipped
    assert client.get("/api/listings-by-ids").json() == []
    assert client.get("/api/listings-by-ids", params=[("ids", 999999)]).json() == []


def test_distance_annotation(client, monkeypatch):
    # avoid network: stub the geocoder used by the listings route
    from app.api.routes import listings as listings_route

    monkeypatch.setattr(
        listings_route,
        "_resolve_origins",
        lambda db, near, city: [(46.77, 23.59, "Test Origin")],
    )
    data = client.get(
        "/api/listings",
        params={"city": "cluj-napoca", "near": "orice", "sort": "distance", "page_size": 60},
    ).json()
    items = data["items"]
    assert items, "expected listings"
    # all annotated, ascending by distance, with a transit maps link
    dists = [i["distance_to_origin_m"] for i in items]
    assert all(d is not None for d in dists)
    assert dists == sorted(dists)
    assert "travelmode=transit" in items[0]["distance_maps_url"]
    assert items[0]["distance_origin_label"] == "Test Origin"
