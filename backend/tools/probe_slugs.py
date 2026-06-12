"""One-off probe script (not part of permanent tooling) to verify per-site
location slugs for storia, olx, imobiliare, publi24 for the 5 new cities.

Run with: .venv\\Scripts\\python.exe tools\\probe_slugs.py
"""
from __future__ import annotations

import re
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}
SLEEP = 1.5


def probe_storia(slug: str) -> tuple[bool, str]:
    url = f"https://www.storia.ro/ro/rezultate/inchiriere/apartament/{slug}?page=1"
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    m = re.search(r'"searchAds"\s*:\s*\{', r.text)
    has_next_data = "__NEXT_DATA__" in r.text
    return bool(m and has_next_data), f"status={r.status_code} __NEXT_DATA__={has_next_data} searchAds={bool(m)} len={len(r.text)}"


def probe_olx(slug: str) -> tuple[bool, str]:
    url = f"https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/{slug}/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    has_state = "__PRERENDERED_STATE__" in r.text
    return has_state, f"status={r.status_code} __PRERENDERED_STATE__={has_state} len={len(r.text)}"


def probe_imobiliare(slug: str) -> tuple[bool, str]:
    url = f"https://www.imobiliare.ro/inchirieri-apartamente/{slug}?pagina=1"
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    count = len(re.findall(r'data-price', r.text))
    return count > 0, f"status={r.status_code} data-price_count={count} len={len(r.text)}"


def probe_publi24(slug: str) -> tuple[bool, str]:
    url = f"https://www.publi24.ro/anunturi/imobiliare/de-inchiriat/apartamente/{slug}/"
    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    count = len(re.findall(r'class="[^"]*article-item', r.text))
    return count > 0, f"status={r.status_code} article-item_count={count} len={len(r.text)}"


PROBES = {
    "storia": probe_storia,
    "olx": probe_olx,
    "imobiliare": probe_imobiliare,
    "publi24": probe_publi24,
}


def run(site: str, candidates: list[str]):
    for slug in candidates:
        try:
            ok, info = PROBES[site](slug)
        except Exception as exc:  # noqa: BLE001
            ok, info = False, f"ERROR: {exc}"
        status = "OK " if ok else "FAIL"
        print(f"[{site}] {slug!r}: {status} -- {info}")
        time.sleep(SLEEP)


CANDIDATES = {
    "storia": {
        "oradea": ["bihor", "oradea"],
        "timisoara": ["timis", "timisoara"],
        "iasi": ["iasi"],
        "targu-mures": ["mures", "targu-mures"],
        "bucuresti": ["mazowieckie"],  # placeholder, replaced below
    },
    "olx": {
        "oradea": ["oradea"],
        "timisoara": ["timisoara"],
        "iasi": ["iasi"],
        "targu-mures": ["targu-mures"],
        "bucuresti": ["bucuresti"],
    },
    "imobiliare": {
        "oradea": ["judetul-bihor/oradea"],
        "timisoara": ["judetul-timis/timisoara"],
        "iasi": ["judetul-iasi/iasi"],
        "targu-mures": ["judetul-mures/targu-mures"],
        "bucuresti": ["bucuresti", "judetul-bucuresti/bucuresti"],
    },
    "publi24": {
        "oradea": ["bihor/oradea"],
        "timisoara": ["timis/timisoara"],
        "iasi": ["iasi/iasi"],
        "targu-mures": ["mures/targu-mures"],
        "bucuresti": ["bucuresti/bucuresti", "bucuresti"],
    },
}

# Fix the storia bucuresti placeholder
CANDIDATES["storia"]["bucuresti"] = ["bucuresti"]


if __name__ == "__main__":
    import sys as _sys
    only_site = _sys.argv[1] if len(_sys.argv) > 1 else None
    for site, cities in CANDIDATES.items():
        if only_site and site != only_site:
            continue
        for city, candidates in cities.items():
            run_label = f"{site}/{city}"
            print(f"=== {run_label} ===")
            run(site, candidates)
