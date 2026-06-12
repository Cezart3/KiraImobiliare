# RentScalper

Romanian rental-listings aggregator: Python scraping worker + FastAPI + React SPA.
Target cities: Cluj-Napoca, Oradea, Timisoara, Iasi, Targu Mures, Bucuresti.

## Layout
- `backend/app/scraping/sites/` — one adapter per source site (contract: `scraping/base.py`; reference impl: `storia.py`). Register new adapters in `sites/__init__.py`.
- `backend/app/scraping/extractors/` — pure-regex Romanian text extraction (parking taxonomy, heating, price, rooms, street). All matching on diacritics-folded text (`core/textutil.fold`).
- `backend/app/scraping/pipeline.py` — RawListing -> extract -> geocode -> upsert (idempotent by URL).
- `backend/app/data/cities/*.json` — source of truth for zones/nearby-towns/site slugs. `verified: false` means centroid not yet confirmed via Nominatim (`backend/tools/geocode_zones.py`).
- `backend/app/services/` — geo (Nominatim + DB cache, budget-capped), matching (parking<->rent rebuild per scrape).
- `backend/app/api/routes/auth.py` + `billing.py` — accounts (email+bcrypt, Google ID token, JWT httpOnly cookie) and Stripe subscription (Checkout/Portal/sync/webhook).
- `frontend/` — Vite + React TS + Tailwind v4 (class-based dark mode); all filter state in URL searchParams; UI text Romanian.

## Commands (backend dir, venv `.venv`)
- Tests: `.venv\Scripts\python.exe -m pytest tests -q`
- API: `.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000`
- One-shot scrape: `.venv\Scripts\python.exe -m app.worker.scheduler --once --city cluj-napoca [--site storia] [--max-pages 2]`
- Scheduler daemon: `.venv\Scripts\python.exe -m app.worker.scheduler`
- Frontend: `npm run dev` in `frontend/` (proxies /api -> :8000)

## Conventions / invariants
- Datetimes: naive UTC everywhere (`models.utcnow()`); SQLite-safe comparisons.
- Listing "active" = `last_seen_at` within `RS_LISTING_ACTIVE_DAYS` (no delete jobs).
- Card click goes to the ORIGINAL listing URL; images go through `/api/img?u=` proxy (host whitelist = adapters' `image_hosts`).
- Parking taxonomy: included / likely_included / area_possible / none / unknown + separate ParkingMatch rows for rentable spots nearby. `is_approx` when either side geocoded at zone/city precision.
- Scrapers must stay polite: PoliteSession (per-host delay), page caps, budget-capped detail fetches; never retry non-200.
- Settings via `.env` at repo root, prefix `RS_` (see `.env.example`).
- Freemium paywall: free users get first `RS_FREE_LISTING_LIMIT` listings, but `total` in `/api/listings` is ALWAYS the real count (product requirement). Gating lives ONLY server-side in `listings.py`; never trust the client.
- Subscription: 15 RON/month Stripe. Cancel must stay one click (Billing Portal). Checkout has an idempotency key + server-side duplicate-subscription check — keep both when touching billing.
- Auth endpoints are rate-limited per IP (`core/ratelimit.py`, in-memory — swap for Redis if multi-worker).
- Account deletion (`/auth/delete-account`) must cancel live Stripe subs first (GDPR erasure without zombie charges).
- Deploy: single Hetzner VPS (Caddy + uvicorn + worker via systemd) — see `docs/DEPLOY.md`. Prod checklist: RS_SECRET_KEY (32+ chars), RS_COOKIE_SECURE=true, RS_ENABLE_ADMIN_ENDPOINTS=false.

## Task delegation (user preference)
Use cheaper-model agents (sonnet/haiku) for: new site adapters (give them `storia.py` + an old-script reference), city data files, frontend components, docs. Keep for the main model: extractor semantics, pipeline/matching changes, API contract changes.
