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
