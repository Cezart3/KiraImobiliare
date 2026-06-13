from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.db.base import SessionLocal, init_db
from app.db.models import Listing, ParkingMatch, ParkingSpot, utcnow
from app.main import app


def _seed() -> None:
    with SessionLocal() as db:
        db.query(ParkingMatch).delete()
        db.query(Listing).delete()
        db.query(ParkingSpot).delete()
        db.commit()

        l1 = Listing(
            site="storia", url="https://x/1",
            title="Ap 2 camere Manastur centrala proprie",
            price_eur=450, rooms=2, city_slug="cluj-napoca", zone_slug="manastur",
            parking_status="included", parking_confidence=3,
            heating="centrala_proprie", images=["https://img/1.jpg"],
            lat=46.75, lon=23.55, geo_precision="zone",
        )
        l2 = Listing(
            site="olx", url="https://x/2", title="Garsoniera Marasti termoficare",
            price_eur=300, rooms=1, city_slug="cluj-napoca", zone_slug="marasti",
            parking_status="area_possible", parking_confidence=2,
            heating="termoficare", lat=46.78, lon=23.61, geo_precision="zone",
        )
        l3 = Listing(
            site="storia", url="https://x/3", title="Ap 3 camere Floresti",
            price_eur=500, rooms=3, city_slug="cluj-napoca", zone_slug=None,
            in_nearby_town=True, town_slug="floresti",
            parking_status="unknown", heating="unknown",
            lat=46.74, lon=23.49, geo_precision="zone",
        )
        stale = Listing(
            site="olx", url="https://x/4", title="Anunt vechi",
            price_eur=400, rooms=2, city_slug="cluj-napoca",
            parking_status="unknown", heating="unknown", geo_precision="none",
            last_seen_at=utcnow() - timedelta(days=30),
        )
        spot = ParkingSpot(
            site="olx", url="https://p/1", title="Loc parcare subteran Manastur",
            price_eur=50, city_slug="cluj-napoca", zone_slug="manastur",
            kind="subteran", lat=46.751, lon=23.552, geo_precision="zone",
        )
        db.add_all([l1, l2, l3, stale, spot])
        db.flush()
        db.add(
            ParkingMatch(
                listing_id=l1.id, parking_id=spot.id,
                distance_m=320, walk_min=5.2, is_approx=True,
            )
        )
        db.commit()


@pytest.fixture(scope="module")
def client():
    init_db()
    _seed()
    with TestClient(app) as c:
        yield c


def _get(client, **params):
    base = {"city": "cluj-napoca"}
    base.update(params)
    r = client.get("/api/listings", params=base)
    assert r.status_code == 200, r.text
    return r.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "db": True}


def test_default_excludes_nearby_and_stale(client):
    data = _get(client)
    assert data["total"] == 2
    urls = {i["url"] for i in data["items"]}
    assert urls == {"https://x/1", "https://x/2"}


def test_include_nearby(client):
    assert _get(client, include_nearby=True)["total"] == 3


def test_price_filter(client):
    data = _get(client, price_max=350)
    assert [i["url"] for i in data["items"]] == ["https://x/2"]


def test_rooms_filter(client):
    data = _get(client, rooms=2)
    assert [i["url"] for i in data["items"]] == ["https://x/1"]


def test_heating_filter(client):
    data = _get(client, heating="centrala_proprie")
    assert [i["url"] for i in data["items"]] == ["https://x/1"]


def test_zone_filter(client):
    data = _get(client, zones="marasti")
    assert [i["url"] for i in data["items"]] == ["https://x/2"]


def test_parking_status_filter(client):
    data = _get(client, parking="included")
    assert [i["url"] for i in data["items"]] == ["https://x/1"]


def test_parking_rentable_nearby(client):
    data = _get(client, parking="rentable_nearby")
    assert [i["url"] for i in data["items"]] == ["https://x/1"]
    item = data["items"][0]
    assert item["parking_match_count"] == 1
    assert item["best_parking"]["distance_m"] == 320
    assert "google.com/maps" in item["best_parking"]["maps_url"]


def test_parking_or_semantics(client):
    data = _get(client, parking=["area_possible", "rentable_nearby"])
    assert data["total"] == 2


def test_sort_price_asc(client):
    data = _get(client, sort="price_asc")
    prices = [i["price_eur"] for i in data["items"]]
    assert prices == sorted(prices)


def test_detail_with_matches(client):
    listing_id = next(
        i["id"] for i in _get(client)["items"] if i["url"] == "https://x/1"
    )
    r = client.get(f"/api/listings/{listing_id}")
    assert r.status_code == 200
    detail = r.json()
    assert len(detail["parking_matches"]) == 1
    assert detail["parking_matches"][0]["is_approx"] is True


def test_cities_meta(client):
    r = client.get("/api/cities")
    assert r.status_code == 200
    cities = {c["slug"]: c for c in r.json()}
    assert "cluj-napoca" in cities
    assert any(z["slug"] == "manastur" for z in cities["cluj-napoca"]["zones"])
    assert any(t["slug"] == "floresti" for t in cities["cluj-napoca"]["nearby_towns"])


def test_upsert_parking_geocodes_without_crash(client):
    # regression: _geolocate signature gained a landmark arg; upsert_parking must
    # pass it (None) so parking spots still geocode instead of raising TypeError.
    from app.core.cities import get_city
    from app.scraping.base import RawListing
    from app.scraping.pipeline import upsert_parking
    from app.services.geo import Geocoder

    with SessionLocal() as db:
        city = get_city("cluj-napoca")
        raw = RawListing(
            site="storia", url="https://test/parking-geo-1",
            title="Loc de parcare subteran Marasti", description="loc parcare",
            price_value="50", price_currency="EUR", location_text="Marasti",
        )
        spot, created, drop = upsert_parking(db, raw, city, Geocoder(db, budget=0))
        assert drop is None and spot is not None  # no TypeError, spot stored
        assert spot.lat is not None and spot.lon is not None  # geocoded (zone centroid)
