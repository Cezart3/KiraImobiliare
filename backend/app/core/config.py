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
    request_delay_s: float = 1.5
    request_timeout_s: int = 25
    max_pages_per_site: int = 10
    detail_fetch_budget: int = 40      # detail-page fetches per site per run
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
    enable_admin_endpoints: bool = True
    admin_token: str = ""              # when set, X-Admin-Token grants admin access
                                       # even with enable_admin_endpoints=false (prod)

    # auth / sessions
    secret_key: str = "dev-secret-change-me"   # set RS_SECRET_KEY in prod!
    session_days: int = 30
    cookie_secure: bool = False                # True behind HTTPS
    google_client_id: str = ""                 # OAuth client ID for "Sign in with Google"
    auth_rate_limit_per_min: int = 20          # auth attempts per IP per minute

    # abuse protection (0 disables a limit)
    global_rate_limit_per_min: int = 600       # per IP, all /api/* routes combined
    img_rate_limit_per_min: int = 400          # per IP, /api/img upstream proxy
    image_cache_max_mb: int = 2000             # disk cap for the image cache (LRU prune)

    # freemium paywall
    paywall_enabled: bool = True
    free_listing_limit: int = 8                # anonymous/free users see this many

    # Stripe (subscription "RentScalper Plus", 15 RON/month)
    stripe_secret_key: str = ""
    stripe_price_id: str = ""                  # price_... for the monthly RON plan
    stripe_webhook_secret: str = ""            # whsec_...
    app_base_url: str = "http://localhost:5173"


settings = Settings()
