"""Application settings. All values overridable via .env (prefix RS_) at repo root."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
REPO_DIR = BACKEND_DIR.parent
VAR_DIR = BACKEND_DIR / "var"
DATA_DIR = BACKEND_DIR / "app" / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_DIR / ".env", env_prefix="RS_", extra="ignore"
    )

    database_url: str = f"sqlite:///{(VAR_DIR / 'rentscalper.db').as_posix()}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # scraping politeness
    user_agent: str = ""               # override the default identifiable UA if a source blocks it
    request_delay_s: float = 1.5
    request_timeout_s: int = 25
    # high cap so a run reaches each site's LAST page (scrapers stop on their own
    # when a site returns no more results) — the goal is ALL current listings, not
    # a sample. Lower it via RS_MAX_PAGES_PER_SITE if you want faster/lighter runs.
    max_pages_per_site: int = 40
    detail_fetch_budget: int = 120     # detail-page fetches per site per run
                                       # (covers thin rows + parking-hint rows whose
                                       #  "inclus in pret" line is folded in the full desc)
    geocode_budget_per_run: int = 80   # new Nominatim lookups per run
    ron_per_eur: float = 5.0           # rough conversion for budget filtering

    # quality filters
    rent_min_eur: int = 120            # below this => parking spot / short-stay noise
    rent_max_eur: int = 15000          # above this => price misparse; keep listing, drop price
    parking_max_eur: int = 200         # above this => mis-listed apartment, not a spot

    # scheduler
    scrape_interval_min: int = 180
    listing_active_days: int = 4       # listing shown while seen within N days

    # parking <-> rent matching
    parking_match_max_m: int = 1000
    parking_matches_per_listing: int = 5
    walk_speed_kmh: float = 4.7
    walk_detour_factor: float = 1.3    # straight-line -> on-foot distance estimate

    # external services
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    ors_api_key: str = ""              # openrouteservice key (optional, real walk routes)

    image_cache_dir: Path = VAR_DIR / "img_cache"

    # abuse protection (0 disables a limit)
    global_rate_limit_per_min: int = 600       # per IP, all /api/* routes combined
    img_rate_limit_per_min: int = 400          # per IP, /api/img upstream proxy
    image_cache_max_mb: int = 2000             # disk cap for the image cache (LRU prune)


settings = Settings()
