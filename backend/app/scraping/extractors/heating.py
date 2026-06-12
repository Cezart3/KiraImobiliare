"""Heating classification: centrala proprie vs termoficare (district/building heating).

User rule: 'termoficare generala / pe bloc' => NOT centrala proprie.
Patterns run on diacritics-folded lowercase text.
"""
import re

from app.core.textutil import fold
from app.db.models import Heating

# phrases where 'central(a)' refers to LOCATION or is ambiguous — removed before matching
_AMBIGUOUS = re.compile(
    r"zona \w{0,12}\s?centrala|pozitie centrala|amplasament central[a]?|"
    r"ultracentral[a]?|parte centrala|incalzire centrala\b(?!\s*propri)"
)

_TERMOFICARE = re.compile(
    r"termoficare|incalzire centralizat|sistem centralizat|"
    r"centrala (?:termica )?de cartier|punct termic|"
    r"\bradet\b|termoenergetica|\bcolterm\b|\bcet\b|"
    r"(?:incalzire|caldura|agent termic|apa calda)\s+(?:de )?la (?:bloc|oras|retea)|"
    r"centrala (?:pe|de) (?:bloc|scara)|centrala comuna|\bpe bloc\b"
)

_PROPRIE_EXPLICIT = re.compile(
    r"centrala (?:termica )?(?:propri|individual)|ct propri|"
    r"centrala (?:de |pe )?apartament|microcentrala|incalzire individual"
)

_PROPRIE_ANY = re.compile(
    r"centrala (?:termica )?(?:propri|individual)|ct propri|"
    r"centrala (?:de |pe )?apartament|microcentrala|incalzire individual|"
    r"centrala (?:pe|de) gaz|centrala noua|\bcentrala termica\b|\bcentrala\b|\bct\b"
)


def classify_heating(text: str) -> Heating:
    t = fold(" ".join((text or "").split()))
    if not t:
        return Heating.UNKNOWN
    t = _AMBIGUOUS.sub(" ", t)
    if _TERMOFICARE.search(t) and not _PROPRIE_EXPLICIT.search(t):
        return Heating.TERMOFICARE
    if _PROPRIE_ANY.search(t):
        return Heating.CENTRALA_PROPRIE
    return Heating.UNKNOWN
