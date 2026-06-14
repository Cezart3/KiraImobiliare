"""Pure parsing tests for site adapters — inline fixtures, no network."""
from bs4 import BeautifulSoup

from app.scraping.extractors.price import PRICE_TEXT_RE
from app.scraping.sites.imobiliare import ImobiliareScraper
from app.scraping.sites.olx import OlxScraper, _extract_js_string, _photo_urls
from app.scraping.sites.publi24 import Publi24Scraper
from app.scraping.sites.storia import StoriaScraper, _next_data, _parse_rooms

# --- olx ----------------------------------------------------------------------

def test_olx_extract_js_string():
    html = 'foo window.__PRERENDERED_STATE__ = "{\\"listing\\":{\\"x\\":1}}"; bar'
    assert _extract_js_string(html, "window.__PRERENDERED_STATE__") == '{"listing":{"x":1}}'


def test_olx_extract_js_string_missing():
    assert _extract_js_string("<html></html>", "window.__PRERENDERED_STATE__") is None


def test_olx_photo_resize():
    photos = [{"link": "https://img.olxcdn.com/a;s=200x100"}, "https://x.olxcdn.com/b;s=64x64"]
    out = _photo_urls(photos)
    assert all(";s=800x600" in u for u in out)


def test_olx_to_raw_skips_jobs():
    assert OlxScraper()._to_raw({"isJob": True, "url": "https://olx.ro/x"}) is None


def test_olx_to_raw_fields():
    raw = OlxScraper()._to_raw(
        {
            "id": 123,
            "url": "https://www.olx.ro/d/oferta/x.html",
            "title": " Ap 2 camere ",
            "description": "<p>Centrala proprie<br>parcare</p>",
            "price": {"regularPrice": {"value": 450, "currencyCode": "EUR"}},
            "location": {"cityName": "Cluj-Napoca", "districtName": "Manastur"},
            "photos": [{"link": "https://img.olxcdn.com/a;s=100x100"}],
        }
    )
    assert raw.title == "Ap 2 camere"
    assert raw.price_value == "450" and raw.price_currency == "EUR"
    assert raw.location_text == "Cluj-Napoca, Manastur"
    assert "Centrala proprie" in raw.description and "<" not in raw.description


# --- storia -------------------------------------------------------------------

def test_storia_next_data():
    html = '<script id="__NEXT_DATA__" type="application/json">{"props":{"a":1}}</script>'
    assert _next_data(html) == {"props": {"a": 1}}


def test_storia_rooms_enum_and_int():
    assert _parse_rooms("TWO") == 2
    assert _parse_rooms(3) == 3
    assert _parse_rooms("weird") is None


def test_storia_to_raw():
    raw = StoriaScraper()._to_raw(
        {
            "id": 9,
            "slug": "ap-2-camere-ID9",
            "title": "Ap 2 camere",
            "shortDescription": "Frumos",
            "totalPrice": {"value": 500, "currency": "EUR"},
            "location": {"address": {"city": {"name": "Cluj-Napoca"}}},
            "tags": [{"value": "GARAGE"}],
            "images": [{"medium": "https://ireland.apollo.olxcdn.com/img.jpg"}],
            "roomsNumber": "TWO",
            "areaInSquareMeters": 54,
        }
    )
    assert raw.url.endswith("/ro/oferta/ap-2-camere-ID9")
    assert raw.parking_hint is True
    assert raw.rooms == 2 and raw.surface_m2 == 54
    assert raw.images == ["https://ireland.apollo.olxcdn.com/img.jpg"]


# --- imobiliare -----------------------------------------------------------------

def test_imobiliare_card_parse():
    html = (
        '<div data-price="450" data-bi-listing-currency="EUR" data-name="Ap 2 camere">'
        '<a href="/oferta/x"></a>2 camere 54 mp Manastur</div>'
    )
    card = BeautifulSoup(html, "html.parser").select_one("div[data-price]")
    raw = ImobiliareScraper()._to_raw(card)
    assert raw.url == "https://www.imobiliare.ro/oferta/x"
    assert raw.price_value == "450" and raw.price_currency == "EUR"
    assert "Manastur" in raw.extra_text


# --- publi24 --------------------------------------------------------------------

def test_publi24_price_regex():
    m = PRICE_TEXT_RE.search("Apartament 2 camere 350 € Cluj-Napoca")
    assert m and m.group(1).strip() == "350"


def test_publi24_card_with_badge_counters_and_price_node():
    html = (
        '<div class="article-item">'
        '<a href="/anunt/y">Promovat 3 24 Penthouse exclusivist</a>'
        '<h2>Penthouse exclusivist</h2>'
        '<div class="article-price">1 500 EUR</div>'
        "</div>"
    )
    card = BeautifulSoup(html, "html.parser").select_one("div.article-item")
    raw = Publi24Scraper()._to_raw(card)
    assert raw.title == "Penthouse exclusivist"
    assert raw.price_value == "1 500"  # -> 1500 EUR, not 41500


def test_publi24_card_parse():
    html = '<div class="article-item"><a href="/anunt/x">Garsoniera Marasti</a> 250 euro </div>'
    card = BeautifulSoup(html, "html.parser").select_one("div.article-item")
    raw = Publi24Scraper()._to_raw(card)
    assert raw.url == "https://www.publi24.ro/anunt/x"
    # alternation matches the 'eur' prefix first — enough for the EUR hint downstream
    assert raw.price_value == "250" and raw.price_currency.lower().startswith("eur")
