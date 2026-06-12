"""One-off: validate OLX location slugs for all cities (catches 'iasi' trap:
plain name resolving to a tiny homonym village instead of the city)."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from app.scraping.http import PoliteSession  # noqa: E402
from app.scraping.sites.olx import _prerendered_state  # noqa: E402

http = PoliteSession()


def probe(slug: str) -> str:
    url = f"https://www.olx.ro/imobiliare/apartamente-garsoniere-de-inchiriat/{slug}/"
    html = http.get_text(url) or ""
    state = _prerendered_state(html)
    if not state:
        return "NO STATE"
    listing = (state.get("listing") or {}).get("listing") or {}
    return f"totalElements={listing.get('totalElements')} pages={listing.get('totalPages')}"


for f in sorted(Path("app/data/cities").glob("*.json")):
    cfg = json.loads(f.read_text(encoding="utf-8"))
    slug = cfg["sites"]["olx"]["location"]
    print(f"{cfg['slug']:14} olx={slug:16} -> {probe(slug)}")
