# Kira — checklist de lansare

Bifează în ordine. Nimic din asta nu necesită cod nou — totul e gata; sunt pașii
externi + verificările de go-live.

## Stare cod (verificat)
- [x] 92 teste backend trec, ruff curat
- [x] Frontend build + eslint curat
- [x] 46/46 verificări e2e live (prin proxy, calea reală a browserului)
- [x] Securitate: fără secrete în bundle, rate limiting, GDPR (telefoane/email
      eliminate), headere de securitate, anti-SSRF la proxy imagini
- [x] Legal: Termeni (IP + anti-scraping + plată unică), Confidențialitate,
      Cookies (accept/refuz + ștergere), Despre (opt-out surse), 404, cookie banner
- [x] Monitorizare: /api/admin dashboard + alerte email
- [x] Model plată: one-time 15 lei / 30 zile, prima lună de lansare gratuită

## Înainte de lansare (extern — tu)

### 1. Domeniu
- [ ] Cumpără **kiraimobiliare.ro** (rotld.ro / registrar) — ~10-12 €/an
- [ ] A-record `@` și `www` → IP-ul serverului Hetzner

### 2. Server (vezi `docs/DEPLOY_STEP_BY_STEP.md` — pas cu pas)
- [ ] Cont Hetzner + server CX23 (Ubuntu 24.04)
- [ ] Cheie SSH adăugată
- [ ] `git clone`, venv, `npm run build`, Caddy + systemd (api + worker)

### 3. `.env` de producție (OBLIGATORIU)
- [ ] `RS_SECRET_KEY=` → `openssl rand -hex 32`
- [ ] `RS_COOKIE_SECURE=true`
- [ ] `RS_ENABLE_ADMIN_ENDPOINTS=false` + `RS_ADMIN_TOKEN=` (alt `openssl rand -hex 32`)
- [ ] `RS_APP_BASE_URL=https://kiraimobiliare.ro`
- [ ] `RS_CORS_ORIGINS=["https://kiraimobiliare.ro"]`
- [ ] `RS_GOOGLE_CLIENT_ID=` (Google Cloud OAuth — opțional, butonul Google apare doar dacă e setat)
- [ ] Alerte: `RS_ALERT_EMAIL` + `RS_SMTP_*` (Gmail App Password)
- [ ] **Stripe: LASĂ GOL la lansare** (prima lună gratis → fără plăți → fără PFA necesar)

### 4. Prima lună GRATIS (cum)
Lansarea cu acces gratuit pentru toți = nu seta cheile Stripe. Cu Stripe neconfigurat,
butonul de plată răspunde politicos „plățile nu sunt configurate" și nimeni nu e taxat.
Sau, ca să nu apară deloc paywall-ul prima lună, setează `RS_PAYWALL_ENABLED=false`
(toți văd tot). Recomand: paywall pornit + Stripe gol → vezi cine vrea să plătească,
dar nu încasezi nimic.

### 5. După ce vezi trafic (activezi plata)
- [ ] Deschide PFA (online ONRC, 1-3 zile, ~gratis)
- [ ] Stripe: produs cu preț **One-time** 15 RON → `RS_STRIPE_PRICE_ID`
- [ ] `RS_STRIPE_SECRET_KEY` (live) + webhook `https://kiraimobiliare.ro/api/billing/webhook`
      (event `checkout.session.completed`) → `RS_STRIPE_WEBHOOK_SECRET`
- [ ] Apple Pay/Google Pay: Stripe → Payment methods → Wallets + domain verification
- [ ] `systemctl restart kira-api`

## La go-live (verificări rapide)
- [ ] `https://kiraimobiliare.ro` se încarcă (landing)
- [ ] `https://kiraimobiliare.ro/api/health` → `{"status":"ok","db":true}`
- [ ] Alege un oraș → vezi anunțuri cu poze
- [ ] Creează cont + login + logout merg
- [ ] `/api/admin` (cu token) → dashboard verde, surse "ok"
- [ ] Rulează un scrape complet o dată: `sudo -u kira .../python -m app.worker.scheduler --once`
- [ ] UptimeRobot pe `/api/health` (alertă dacă pică)

## După lansare
- [ ] Postează pe LinkedIn (text + `docs/promo/linkedin-listings-dark.png`)
- [ ] Urmărește `/api/admin` zilnic în prima săptămână
- [ ] Răspunde la emailul OLX (caz #24175627) dacă vine
- [ ] Extrasezon: `systemctl stop kira-*` + snapshot Hetzner (economisești)

## Costuri
- Hetzner CX23: ~4 €/lună (poți opri extrasezon)
- Domeniu: ~10 €/an
- Stripe: doar comision per tranzacție (~1.5% + 0.25 €), zero lunar
- **Total în sezon: ~5 €/lună.** Restul anului: doar domeniul.
