from app.db.models import Heating, ParkingKind, ParkingStatus
from app.scraping.extractors.address import extract_street, has_house_number
from app.scraping.extractors.heating import classify_heating
from app.scraping.extractors.parking import (
    classify_parking,
    classify_parking_spot,
    looks_like_parking_only,
)
from app.scraping.extractors.price import to_eur
from app.scraping.extractors.rooms import extract_floor, extract_rooms, extract_surface

# --- parking taxonomy ---------------------------------------------------------

def test_parking_included():
    s, c = classify_parking("Apartament cu loc de parcare inclus în preț")
    assert s == ParkingStatus.INCLUDED and c == 3


def test_parking_included_subteran():
    s, _ = classify_parking("2 camere, parcare subterană")
    assert s == ParkingStatus.INCLUDED


def test_parking_area_possible():
    s, _ = classify_parking("Posibilitate de parcare în zonă")
    assert s == ParkingStatus.AREA_POSSIBLE


def test_parking_area_free_unmarked():
    s, _ = classify_parking("parcare la liber, locuri nemarcate în fața blocului")
    assert s == ParkingStatus.AREA_POSSIBLE


def test_parking_extra_cost_is_area():
    s, _ = classify_parking("loc de parcare contra cost în subteran")
    assert s == ParkingStatus.AREA_POSSIBLE


def test_parking_none():
    s, _ = classify_parking("apartament fără loc de parcare")
    assert s == ParkingStatus.NONE


def test_parking_unknown():
    s, c = classify_parking("Apartament 2 camere lângă parc")  # 'parc' != 'parcare'
    assert s == ParkingStatus.UNKNOWN and c == 0


def test_parking_structured_hint_upgrades():
    s, c = classify_parking("Apartament frumos", structured_hint=True)
    assert s == ParkingStatus.INCLUDED and c >= 2


def test_parking_spot_kind():
    kind, numbered = classify_parking_spot("Închiriez loc parcare subteran nr. 24")
    assert kind == ParkingKind.SUBTERAN and numbered


def test_parking_only_title():
    assert looks_like_parking_only("Închiriez loc de parcare Mărăști")
    assert not looks_like_parking_only("Apartament 2 camere cu loc de parcare")


# --- heating ------------------------------------------------------------------

def test_heating_proprie():
    assert classify_heating("centrală termică proprie") == Heating.CENTRALA_PROPRIE


def test_heating_termoficare():
    assert classify_heating("încălzire prin termoficare") == Heating.TERMOFICARE


def test_heating_pe_bloc():
    assert classify_heating("căldură de la bloc, apă caldă") == Heating.TERMOFICARE


def test_heating_centralizat():
    assert classify_heating("încălzire centralizată RADET") == Heating.TERMOFICARE


def test_heating_zona_centrala_not_heating():
    assert classify_heating("apartament în zonă centrală, lângă parc") == Heating.UNKNOWN


def test_heating_ultracentral_with_centrala():
    assert (
        classify_heating("ultracentral, cu centrală proprie") == Heating.CENTRALA_PROPRIE
    )


def test_heating_bare_centrala():
    assert classify_heating("mobilat, utilat, centrală, AC") == Heating.CENTRALA_PROPRIE


def test_heating_unknown():
    assert classify_heating("apartament luminos cu balcon") == Heating.UNKNOWN


# --- price --------------------------------------------------------------------

def test_price_eur_symbol():
    assert to_eur("450 €") == 450.0


def test_price_ron_converted():
    assert to_eur("2.500 lei", ron_per_eur=5.0) == 500.0


def test_price_currency_hint():
    assert to_eur("1500", currency_hint="RON", ron_per_eur=5.0) == 300.0


def test_price_thousands_dot():
    assert to_eur("1.200 EUR") == 1200.0


def test_price_garbage():
    assert to_eur("la cerere") is None


# --- rooms / surface / floor ----------------------------------------------------

def test_rooms_numeric():
    assert extract_rooms("Apartament 2 camere decomandat") == 2


def test_rooms_garsoniera():
    assert extract_rooms("Garsonieră confort 1") == 1


def test_surface():
    assert extract_surface("suprafață 54 mp utili") == 54.0


def test_floor():
    assert extract_floor("etaj 3 din 4") == "3"


# --- address ------------------------------------------------------------------

def test_street_with_number():
    s = extract_street("Inchiriez apartament str. Fabricii nr. 105, zona Iris")
    assert "fabricii" in s.lower()
    assert has_house_number(s)


def test_street_stopword_truncation():
    s = extract_street("strada Memorandumului compus din 2 camere")
    assert s.lower() == "strada memorandumului"


def test_street_none():
    assert extract_street("apartament frumos in cartier linistit") == ""


# ---------- price text anchoring (publi24 badge-counter bug) ----------


def test_find_price_text_ignores_glued_counters():
    from app.scraping.extractors.price import find_price_text, to_eur

    def parse(s):
        f = find_price_text(s)
        return to_eur(f[0], f[1]) if f else None

    assert parse("04 1 500 EUR") == 1500          # was 41500
    assert parse("05 250 EUR") == 250             # was 5250
    assert parse("Promovat 3 24 Apartament 2 cam 550 EUR") == 550
    assert parse("550 EUR") == 550
    assert parse("1.500 eur") == 1500
    assert parse("1 500 EUR") == 1500
    assert parse("2 000 lei") == 400              # 5 RON/EUR default
    assert parse("fara pret") is None


def test_negotiable_flag_detection():
    import re

    from app.core.textutil import fold

    neg = re.compile(r"\bnegocia")
    assert neg.search(fold("Pret 350 EUR negociabil"))
    assert neg.search(fold("usor negociabil!"))
    assert not neg.search(fold("pret fix nenegociabil"))
    assert not neg.search(fold("apartament 2 camere"))


def test_to_eur_separator_disambiguation():
    from app.scraping.extractors.price import to_eur

    assert to_eur("1.500 eur") == 1500          # RO thousands
    assert to_eur("906.29 EUR") == 906.3        # decimal dot (imobiliare)
    assert to_eur("3023.79 eur") == 3023.8
    assert to_eur("1,000", "EUR") == 1000       # EN thousands (capital)
    assert to_eur("906,29 eur") == 906.3        # decimal comma
    assert to_eur("1.234.567 eur") == 1234567
    assert to_eur("2 000 lei") == 400


# ---------- parking: real-world phrasings that were misclassified ----------


def test_parking_include_multiword_gap():
    # "pretul include si un loc de parcare..." — words between include & parcare
    s, _ = classify_parking("Pretul include si un loc de parcare in fata blocului")
    assert s == ParkingStatus.INCLUDED


def test_parking_dispune_de_loc():
    s, _ = classify_parking("Apartamentul dispune de un loc de parcare langa bloc")
    assert s == ParkingStatus.INCLUDED


def test_parking_negated_dispune_is_not_included():
    s, _ = classify_parking("Apartamentul nu dispune de loc de parcare")
    assert s == ParkingStatus.NONE


def test_parking_area_plus_no_own_spot_stays_area():
    # has area parking but no OWN spot -> area_possible, not none, not included
    s, _ = classify_parking(
        "Exista posibilitate de parcare in zona, insa apartamentul nu dispune "
        "de loc propriu de parcare"
    )
    assert s == ParkingStatus.AREA_POSSIBLE


def test_parking_stradala_is_area():
    s, _ = classify_parking("Parcare stradala pe baza de abonament lunar")
    assert s == ParkingStatus.AREA_POSSIBLE


def test_needs_enrich_parking_hint():
    # storia hides "loc de parcare inclus in pret" behind a fold; a listing with
    # a decent snippet + images but weak parking status, whose title mentions
    # parking, must still be queued for a full-description fetch.
    from app.worker.jobs import _needs_enrich

    class L:
        def __init__(self, title, desc, status, images, geo="exact"):
            self.title = title
            self.description = desc
            self.parking_status = status
            self.images = images
            self.geo_precision = geo

    long_desc = "x" * 250
    # weak status + parking in title -> enrich
    assert _needs_enrich(L("Apartament 3 camere parcare", long_desc, "likely_included", ["a"]))
    assert _needs_enrich(L("Garsoniera cu garaj", long_desc, "unknown", ["a"]))
    # already strong -> no need
    assert not _needs_enrich(L("Apartament parcare", long_desc, "included", ["a"]))
    # no parking hint, rich enough -> no need
    assert not _needs_enrich(L("Apartament 2 camere", long_desc, "unknown", ["a"]))
    # thin desc always enriches
    assert _needs_enrich(L("Apartament", "scurt", "included", ["a"]))
    # weak geo + street mention -> enrich to pin the exact address
    assert _needs_enrich(L("Apartament strada Cojocnei", long_desc, "included", ["a"], geo="zone"))
    # weak geo, no street mention -> no need
    assert not _needs_enrich(L("Apartament zona buna", long_desc, "included", ["a"], geo="zone"))


def test_find_landmark_cluj():
    from app.core.cities import find_landmark, get_city

    c = get_city("cluj-napoca")
    assert find_landmark(c, "Marasti/Kaufland/Anina").slug == "kaufland-marasti"
    assert find_landmark(c, "zona Expo Transilvania").slug == "expo-transilvania"
    assert find_landmark(c, "langa Iulius Mall").slug == "iulius-mall"
    assert find_landmark(c, "apartament fara reper in Manastur") is None
