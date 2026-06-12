# Deploy — varianta ieftină (recomandat: totul pe Hetzner)

## Vercel + Hetzner sau doar Hetzner?

Recomandarea scurtă: **doar Hetzner**. Motivele:

- Vercel găzduiește excelent frontend-uri statice (gratis), dar **nu poate rula partea
  importantă a proiectului**: workerul de scraping e un proces care rulează continuu
  (APScheduler), iar SQLite are nevoie de disc persistent. Pe Vercel funcțiile sunt
  serverless (pornesc/mor la request) — scraperul n-are unde trăi.
- Dacă pui frontend pe Vercel și API pe Hetzner ajungi pe **domenii diferite** →
  cookie-ul de sesiune (SameSite=Lax) și CORS devin complicate fără niciun câștig.
- Frontend-ul nostru e un folder de fișiere statice după `npm run build` — orice
  server web îl servește; nu are nevoie de Vercel.

Un singur VPS Hetzner duce lejer tot: API + worker + SQLite + fișierele statice.

**Cost total: ~4–5 €/lună** (VPS CX22: 2 vCPU/4 GB ~3.8 €/lună sau CAX11 ARM ~3.3 €/lună)
**+ domeniu ~10 €/an**. Atât. Postgres nu e necesar la scara asta (SQLite în WAL ține
sute de mii de anunțuri); când crește traficul, `RS_DATABASE_URL` mută totul pe Postgres.

## Arhitectura pe server

```
internet ── Caddy (HTTPS automat, port 443)
              ├── /api/*  → uvicorn pe 127.0.0.1:8000
              └── /*      → /srv/rentscalper/frontend/dist (fișiere statice)
   systemd: rentscalper-api.service  + rentscalper-worker.service
   date:    /srv/rentscalper/backend/var/rentscalper.db (SQLite WAL)
```

## Pași (Ubuntu 24.04, o singură dată, ~30 min)

```bash
# 1. server
apt update && apt install -y python3.12-venv git caddy
adduser --system --group rentscalper

# 2. cod
git clone https://github.com/Cezart3/RentForYou.git /srv/rentscalper
cd /srv/rentscalper/backend
python3.12 -m venv .venv && .venv/bin/pip install -e .

# 3. frontend (build local pe PC sau pe server dacă instalezi node)
cd ../frontend && npm ci && npm run build    # produce frontend/dist

# 4. config
cp /srv/rentscalper/.env.example /srv/rentscalper/.env
# editează .env — OBLIGATORIU în producție:
#   RS_SECRET_KEY=<openssl rand -hex 32>
#   RS_COOKIE_SECURE=true
#   RS_APP_BASE_URL=https://domeniul-tau.ro
#   RS_CORS_ORIGINS=["https://domeniul-tau.ro"]
#   RS_ENABLE_ADMIN_ENDPOINTS=false
#   RS_STRIPE_SECRET_KEY / RS_STRIPE_PRICE_ID / RS_STRIPE_WEBHOOK_SECRET
#   RS_GOOGLE_CLIENT_ID
chown -R rentscalper:rentscalper /srv/rentscalper
```

`/etc/systemd/system/rentscalper-api.service`:

```ini
[Unit]
Description=RentScalper API
After=network.target

[Service]
User=rentscalper
WorkingDirectory=/srv/rentscalper/backend
ExecStart=/srv/rentscalper/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

`/etc/systemd/system/rentscalper-worker.service` — identic, dar:

```ini
ExecStart=/srv/rentscalper/backend/.venv/bin/python -m app.worker.scheduler
```

`/etc/caddy/Caddyfile` (Caddy ia singur certificat Let's Encrypt):

```
domeniul-tau.ro {
    encode gzip
    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }
    handle {
        root * /srv/rentscalper/frontend/dist
        try_files {path} /index.html
        file_server
    }
}
```

```bash
systemctl enable --now rentscalper-api rentscalper-worker
systemctl reload caddy
```

## De ce nu poți primi o factură-surpriză

Hetzner Cloud are **preț fix lunar**: un CX22 costă același ~4 € indiferent câte
cereri primește. Nu e model "pay per request" ca la AWS Lambda/Vercel Functions.
Singurul cost variabil este traficul peste **20 TB/lună incluși** (~1 €/TB peste) —
20 TB înseamnă ~62 Mbps non-stop, o lună întreagă; nu se atinge organic.

Straturi de protecție la abuz (deja în cod):

| Strat | Limita | Unde |
|---|---|---|
| Rate limit global | 600 cereri/min/IP pe tot /api | middleware `app/main.py` |
| Auth (bcrypt = CPU scump) | 20/min/IP | `routes/auth.py` |
| Checkout Stripe | 10/min/IP + idempotency key | `routes/billing.py` |
| Proxy imagini (singurul egress real) | 400/min/IP la cache-miss, max 8 MB/imagine, doar hosturile CDN whitelistate, cache disk plafonat la 2 GB (LRU) | `routes/images.py` |
| Frontend | debounce 400 ms la căutare, fără retry pe erori 4xx | `App.tsx`, `Header.tsx` |

Recomandare suplimentară (gratuită): pune **Cloudflare Free** în fața domeniului
(DNS proxied). Câștigi: absorbție DDoS L3/L7 înainte să atingă VPS-ul, cache global
pe imagini (au `Cache-Control` setat — Cloudflare le servește el, traficul tău
scade dramatic), IP-ul serverului ascuns. Setare: domeniu în Cloudflare → A-record
"proxied" → în Caddyfile rămâne identic. Cu Cloudflare în față, scenariul "factură
din trafic" devine practic imposibil.

În Caddyfile, adaugă și o limită de corp de cerere (apărare suplimentară):

```
    request_body {
        max_size 1MB
    }
```

## Monitorizare (după deploy)

- **Sănătate**: `curl https://domeniu/api/health` → `{"status":"ok","db":true}`
  (uptime monitoring gratuit: UptimeRobot pe acest URL, alertă pe email).
- **Metrici operaționale**: setează `RS_ADMIN_TOKEN` în `.env`, apoi:
  `curl -H "X-Admin-Token: <token>" https://domeniu/api/admin/stats`
  → anunțuri active per oraș, **prospețimea fiecărei surse** (`newest_seen_min_ago` —
  dacă o sursă urcă peste câteva ore, adapterul ei e stricat), erori de scrape din
  ultimele 24h, număr utilizatori/abonați.
- **Loguri**: `journalctl -u rentscalper-api -f` și `journalctl -u rentscalper-worker -f`.
- **Capacitate măsurată** (load test `backend/tools/load_test.py`, mix realist de
  filtre): ~165 req/s pe un singur proces, p95 < 0,8 s la 100 de cereri concurente,
  0 erori. La 1000 de utilizatori/zi (~50k cereri) serverul stă sub 1% utilizare —
  un CX22 e suficient cu marjă mare.

## După deploy (checklist extern)

1. **DNS**: A-record domeniu → IP-ul VPS-ului.
2. **Stripe**: cheile LIVE în `.env`; webhook `https://domeniu/api/billing/webhook`
   (events: `checkout.session.completed`, `customer.subscription.*`); Apple Pay:
   Payment methods → Wallets + Payment method domains → adaugă domeniul.
3. **Google Sign-In**: în Google Cloud Console adaugă `https://domeniul-tau.ro` la
   Authorized JavaScript origins ale clientului OAuth.
4. **Backup**: cron zilnic `sqlite3 rentscalper.db ".backup /backup/rs-$(date +%F).db"`
   (sau snapshot Hetzner, ~1 €/lună).
5. **Update-uri**: `git pull && systemctl restart rentscalper-api rentscalper-worker`
   (+ `npm run build` când se schimbă frontend-ul).

## Worker pe Windows (până faci deploy)

Local, baza rămâne proaspătă doar cât rulează daemonul:

```powershell
cd backend
.venv\Scripts\python.exe -m app.worker.scheduler
```
