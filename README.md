# RentScalper

Aggregator de chirii pentru Romania — un singur loc de cautare peste mai multe site-uri de imobiliare, cu filtre pe care site-urile sursa nu le au: **centrala proprie vs termoficare**, **parcare inclusa / posibilitate de parcare in zona**, si **matching cu anunturi de inchiriat locuri de parcare** din apropiere (distanta de mers pe jos).

Orase: Cluj-Napoca, Oradea, Timisoara, Iasi, Targu Mures, Bucuresti (+ localitati invecinate optionale, ex. Floresti/Baciu pentru Cluj).

## Arhitectura

```
backend/  (Python 3.12+)
  app/scraping/sites/      adaptoare per site (storia, olx, imobiliare, publi24, ...)
  app/scraping/extractors/ regex RO: parcare, incalzire, pret, camere, strada
  app/scraping/pipeline.py normalizare -> extractie -> geocodare -> upsert
  app/services/            geo (Nominatim + cache), matching parcare<->chirie
  app/api/                 FastAPI: /api/listings, /api/parking, /api/cities, /api/img,
                           /api/auth/* (email+parola, Google), /api/billing/* (Stripe)
  app/worker/              APScheduler: scrape periodic per oras, esalonat
  app/data/cities/*.json   zone/cartiere + localitati invecinate + slug-uri per site
frontend/ (Vite + React + TS + Tailwind)  SPA, filtre in URL, UI romana
```

Fluxul: worker-ul scrape-uieste periodic -> DB (SQLite implicit, Postgres optional) -> API-ul serveste instant -> SPA afiseaza. Click pe card = redirect la anuntul original; pozele trec prin proxy-ul `/api/img` (CDN-urile blocheaza hotlink).

## Quickstart

```powershell
# backend
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest tests -q            # sanity
.venv\Scripts\python.exe -m app.worker.scheduler --once --city cluj-napoca --max-pages 3
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# frontend (alt terminal)
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxy /api -> :8000)

# worker continuu (alt terminal)
cd backend
.venv\Scripts\python.exe -m app.worker.scheduler
```

Configurare: copiaza `.env.example` -> `.env` (prefix `RS_`). Postgres optional: `docker compose up -d postgres`.

## Surse de date

| Site | Acoperire | Metoda |
|---|---|---|
| storia.ro | national | `__NEXT_DATA__` JSON (chirii + garaje) |
| olx.ro | national | `__PRERENDERED_STATE__` JSON (chirii + parcari prin cautari) |
| imobiliare.ro | national | HTML cards |
| publi24.ro | national | HTML cards + ld+json |
| lajumate.ro | national | `__NEXT_DATA__` JSON |
| capitalimobiliare.ro | Cluj | HTML |
| extra per oras | vezi `docs/SITE_RESEARCH.md` | piata-az.ro, imopuls.ro, upimobiliare.ro, ... |

**Nota legala**: proiect personal/educational. Scraping politicos (delay-uri, cap de pagini, cache), datele raman la sursa — site-ul doar indexeaza si trimite click-ul inapoi la anuntul original. Inainte de monetizare verifica ToS-urile surselor si OSM/Nominatim usage policy.

## Anunturi mereu la zi (nu e "one-time scrape")

Daemonul `python -m app.worker.scheduler` re-scrapeaza **fiecare oras la `RS_SCRAPE_INTERVAL_MIN` minute** (implicit 180), esalonat ca sa nu loveasca site-urile simultan. Site-urile sursa listeaza cele mai noi anunturi pe prima pagina, deci fiecare trecere prinde tot ce a aparut intre timp. Anunturile existente primesc `last_seen_at` la fiecare trecere; un anunt dispare din UI doar daca nu a mai fost vazut de `RS_LISTING_ACTIVE_DAYS` zile (adica a fost retras la sursa). In productie daemonul ruleaza ca serviciu systemd (vezi `docs/DEPLOY.md`) — atata timp cat serviciul e pornit, baza e mereu proaspata.

## Cont, paywall si plati

- **Cont**: email + parola (bcrypt) sau **Sign in with Google** (`RS_GOOGLE_CLIENT_ID`). Sesiunea = JWT in cookie httpOnly/SameSite=Lax — nimic sensibil in JavaScript.
- **Freemium**: utilizatorii fara abonament vad primele `RS_FREE_LISTING_LIMIT` (implicit 8) anunturi, dar **numarul total gasit e afisat mereu**.
- **Abonament**: 15 lei/luna prin **Stripe Checkout** (card + **Apple Pay/Google Pay** — se activeaza din dashboardul Stripe la Payment methods → Wallets). Anularea e la fel de simpla ca abonarea: buton "Gestioneaza abonamentul" → **Stripe Billing Portal** → Cancel.
- **Setup Stripe** (o singura data): creeaza produs cu pret recurent 15 RON/luna → `RS_STRIPE_PRICE_ID`; cheia secreta → `RS_STRIPE_SECRET_KEY`; in productie adauga webhook `https://<domeniu>/api/billing/webhook` → `RS_STRIPE_WEBHOOK_SECRET`. Local nu ai nevoie de webhook: dupa plata, frontendul apeleaza `/api/billing/sync`.
- **Anti dubla-plata**: butonul de plata se dezactiveaza cat timp cererea e in zbor, checkout-ul foloseste cheie de idempotenta Stripe (dublu-click = aceeasi sesiune de plata), iar serverul refuza checkout daca exista deja abonament activ (verifica si la Stripe, nu doar local).

## Cum functioneaza matching-ul de parcare

1. Se scrape-uiesc separat anunturile de inchiriere *locuri de parcare/garaje*.
2. Chiriile si parcarile se geocodeaza (strada via Nominatim, altfel centroid de cartier).
3. Se calculeaza perechi la < `RS_PARKING_MATCH_MAX_M` (implicit 1000 m), top 5 per chirie, cu timp de mers pe jos estimat si link Google Maps de ruta.
4. Daca vreo coordonata e la nivel de cartier (anuntul nu da adresa exacta), match-ul e marcat **"distanta aproximativa"** — exact cum cere produsul.

## Roadmap
- [ ] Alembic migrations (acum: `create_all`)
- [ ] Rute de mers pe jos reale (openrouteservice / OSRM, cheia `RS_ORS_API_KEY`)
- [ ] Dedup vizual intre surse (`dedup_group` exista deja in API)
- [ ] Harta (Leaflet) cu pin-uri chirii + parcari
- [ ] Adaptoare extra din `docs/SITE_RESEARCH.md` (lajumate, piata-az, imopuls, ...)
- [ ] Deploy (Dockerfile backend + static frontend + Postgres)
