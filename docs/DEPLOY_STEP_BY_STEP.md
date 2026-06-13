# Deploy Kira — pas cu pas, de la zero

Ghid complet pentru cineva care n-a făcut niciodată deploy. Urmează în ordine.
Costuri totale: **~4 €/lună (Hetzner) + ~10 €/an (domeniu)**. Stripe ia comision per
tranzacție (~1.5% + 0.25 €), nimic lunar.

Legendă: `█ TU` = faci tu în browser/cont. `$` = comandă în terminal SSH (copy-paste).

---

## PARTEA 0 — De ce ai nevoie înainte (15 min)

### 0.1 Cumpără un domeniu  █ TU
- Mergi la un registrar ieftin: **Cloudflare Registrar** (la preț de cost, fără
  markup) sau **Namecheap** / **porkbun.com**.
- Caută un `.ro` (~10–12 €/an la registrar RO ca rotld.ro) sau un `.com` (~10 €/an).
  `.com` e cel mai simplu internațional; `.ro` e local.
- Cumpără-l. Notează-l. În acest ghid îl numesc `kiraimobiliare.ro` — înlocuiește peste tot
  cu al tău.
- NU cumpăra add-on-uri (privacy uneori e gratis, restul nu-ți trebuie).

### 0.2 Cont Hetzner Cloud  █ TU
- Mergi la **https://www.hetzner.com/cloud** → "Sign Up".
- Verificare cont: Hetzner cere uneori verificare de identitate la primul cont
  (poate dura câteva ore — fă asta din timp). Adaugă o metodă de plată (card sau
  PayPal).
- După login intri în **Hetzner Cloud Console** (console.hetzner.cloud).

### 0.3 Cont Stripe  █ TU (ai deja, în test mode — OK pentru acum)
- Pentru bani reali ai nevoie de "activare cont" (date firmă/PFA + IBAN). Vezi
  PARTEA 7. Până atunci mergem pe **test mode**, totul funcționează identic.

---

## PARTEA 1 — Cheie SSH (ca să intri în server fără parolă) (5 min)

Pe PC-ul tău Windows, în PowerShell:

```powershell
# generează o cheie (Enter la toate întrebările, fără passphrase e ok pentru început)
ssh-keygen -t ed25519 -C "kira-deploy"
# arată cheia PUBLICĂ (asta o dai lui Hetzner — e SIGUR să o arăți)
type $env:USERPROFILE\.ssh\id_ed25519.pub
```

Copiază tot ce afișează ultima comandă (începe cu `ssh-ed25519 ...`).
⚠️ Cheia PRIVATĂ (`id_ed25519`, fără `.pub`) NU se dă nimănui niciodată.

---

## PARTEA 2 — Creează serverul  █ TU în Hetzner Console (5 min)

1. Console → **Add Server**.
2. **Location**: Nuremberg/Falkenstein (UE, aproape de RO).
3. **Image**: **Ubuntu 24.04**.
4. **Type**: tab **Shared vCPU** → **CX22** (2 vCPU, 4 GB, ~3.8 €/lună). Suficient
   cu marjă mare pentru >1000 utilizatori/zi.
5. **SSH key**: → "Add SSH key" → lipește cheia PUBLICĂ din Partea 1 → Add.
6. **Name**: `kira`.
7. **Create & Buy now**.
8. După ~30 sec ai un **IP public** (ex. `203.0.113.45`). Notează-l → în ghid `IP_SERVER`.

---

## PARTEA 3 — Leagă domeniul de server (DNS)  █ TU (5 min + propagare)

La registrarul unde ai cumpărat domeniul, în secțiunea DNS, adaugă 2 înregistrări:

| Type | Name | Value          |
|------|------|----------------|
| A    | `@`  | `IP_SERVER`    |
| A    | `www`| `IP_SERVER`    |

Salvează. Propagarea durează de la câteva minute la câteva ore. Verifici cu:

```powershell
nslookup kiraimobiliare.ro
```
Când îți răspunde cu `IP_SERVER`, e gata.

> Opțional dar recomandat: pune domeniul pe **Cloudflare** (plan Free) ca să ai
> protecție DDoS + cache. Dacă faci asta, lasă proxy-ul "DNS only" (nor gri) la
> primul deploy ca Caddy să poată lua certificatul, apoi îl pui pe "Proxied".
> Putem face asta împreună după ce merge varianta de bază.

---

## PARTEA 4 — Intră pe server și pregătește-l (10 min)

Din PowerShell pe PC-ul tău:

```powershell
ssh root@IP_SERVER
```
(prima dată întreabă "are you sure" → scrie `yes`). Acum ești PE server. Comenzile
următoare (`$`) se rulează acolo:

```bash
# actualizează sistemul
apt update && apt upgrade -y

# instalează ce ne trebuie: python, git, caddy (web server cu HTTPS automat), node
apt install -y python3.12-venv git curl
# Node.js 20 (pentru build-ul frontend pe server)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
# Caddy (din repo oficial)
apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt update && apt install -y caddy

# user dedicat (nu rulăm app ca root)
adduser --system --group kira
```

---

## PARTEA 5 — Pune codul, configurează, pornește (15 min)

Tot pe server:

```bash
# clonează codul
git clone https://github.com/Cezart3/RentForYou.git /srv/kira
cd /srv/kira

# backend: mediu virtual + dependențe
cd backend
python3.12 -m venv .venv
./.venv/bin/pip install -e .

# frontend: build (produce fișiere statice în frontend/dist)
cd ../frontend
npm ci
npm run build
```

### 5.1 Fișierul de configurare `.env`

```bash
cd /srv/kira
cp .env.example .env
# generează un secret tare pentru sesiuni:
openssl rand -hex 32
# copiază rezultatul, apoi editează .env:
nano .env
```

În `nano` setează (minim):
```
RS_SECRET_KEY=<lipește secretul de la openssl>
RS_COOKIE_SECURE=true
RS_APP_BASE_URL=https://kiraimobiliare.ro
RS_CORS_ORIGINS=["https://kiraimobiliare.ro"]
RS_ENABLE_ADMIN_ENDPOINTS=false
RS_ADMIN_TOKEN=<rulează încă un `openssl rand -hex 32` și pune aici>

# Stripe (test mode pentru acum — le iei din dashboard.stripe.com):
RS_STRIPE_SECRET_KEY=sk_test_...
RS_STRIPE_PRICE_ID=price_...
RS_STRIPE_WEBHOOK_SECRET=whsec_...      # îl obținem la pasul 6.3

# Google login (opțional, îl adăugăm la PARTEA 8):
RS_GOOGLE_CLIENT_ID=
```
Salvează în nano: `Ctrl+O`, Enter, `Ctrl+X`.

```bash
# dă fișierele pe seama userului dedicat
chown -R kira:kira /srv/kira
```

### 5.2 Servicii systemd (pornesc automat, repornesc la crash/reboot)

```bash
# API
cat > /etc/systemd/system/kira-api.service <<'EOF'
[Unit]
Description=Kira API
After=network.target

[Service]
User=kira
WorkingDirectory=/srv/kira/backend
ExecStart=/srv/kira/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Worker (scraping periodic — ține anunțurile la zi)
cat > /etc/systemd/system/kira-worker.service <<'EOF'
[Unit]
Description=Kira scraping worker
After=network.target

[Service]
User=kira
WorkingDirectory=/srv/kira/backend
ExecStart=/srv/kira/backend/.venv/bin/python -m app.worker.scheduler
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now kira-api kira-worker
# verifică:
systemctl status kira-api --no-pager
curl -s http://127.0.0.1:8000/api/health    # trebuie {"status":"ok","db":true}
```

### 5.3 Caddy (HTTPS automat + servește totul)

```bash
cat > /etc/caddy/Caddyfile <<'EOF'
kiraimobiliare.ro, www.kiraimobiliare.ro {
    encode gzip
    request_body {
        max_size 2MB
    }
    handle /api/* {
        reverse_proxy 127.0.0.1:8000
    }
    handle {
        root * /srv/kira/frontend/dist
        try_files {path} /index.html
        file_server
    }
}
EOF
# ÎNLOCUIEȘTE kiraimobiliare.ro cu domeniul tău în fișierul de mai sus (nano /etc/caddy/Caddyfile)
systemctl reload caddy
```

Caddy ia singur certificat HTTPS de la Let's Encrypt (gratuit). Deschide
**https://kiraimobiliare.ro** în browser → trebuie să vezi site-ul. 🎉

### 5.4 Prima populare cu anunțuri

```bash
# rulează un scrape pe toate orașele acum (workerul oricum o face periodic)
sudo -u kira /srv/kira/backend/.venv/bin/python \
  -m app.worker.scheduler --once
```

---

## PARTEA 6 — Stripe (test mode → demo funcțional) (10 min)  █ TU

### 6.1 Produs + preț
- dashboard.stripe.com (colț stânga-sus comută pe **Test mode**).
- Products → Add product → nume "Kira Plus" → preț **recurring**, **15 RON**,
  **monthly** → Save. Copiază **Price ID** (`price_...`) → în `.env` `RS_STRIPE_PRICE_ID`.

### 6.2 Cheie secretă
- Developers → API keys → copiază **Secret key** (`sk_test_...`) → `.env`
  `RS_STRIPE_SECRET_KEY`.

### 6.3 Webhook (ca abonamentele să se sincronizeze automat)
- Developers → Webhooks → Add endpoint:
  - URL: `https://kiraimobiliare.ro/api/billing/webhook`
  - Events: `checkout.session.completed`, `customer.subscription.created`,
    `customer.subscription.updated`, `customer.subscription.deleted`
  - Add endpoint → copiază **Signing secret** (`whsec_...`) → `.env`
    `RS_STRIPE_WEBHOOK_SECRET`.

```bash
# după ce ai pus cheile în .env:
nano /srv/kira/.env        # editezi
systemctl restart kira-api  # reîncarcă config
```

### 6.4 Test plată
- Pe site → cont nou → "Deblochează tot" → la Stripe folosește cardul de test
  `4242 4242 4242 4242`, dată viitoare, orice CVC. Trebuie să te întoarcă abonat.

---

## PARTEA 7 — Trecerea la BANI REALI (când ești gata)  █ TU

Diferența test → live e mică:
1. **Activează contul Stripe**: dashboard → Activate account → completezi date
   (PFA/SRL recomandat pentru încasări recurente; persoană fizică se poate dar
   verifică fiscal), IBAN pentru payout.
2. Comută dashboard pe **Live mode**, refă pasul 6.1–6.3 (produs + chei + webhook
   sunt SEPARATE în live) → pune cheile `sk_live_...`, `price_...` (live),
   `whsec_...` (live) în `.env` → `systemctl restart kira-api`.
3. **Apple Pay / Google Pay**: Stripe → Settings → Payment methods → activează
   Wallets. Pentru Apple Pay: Settings → Payment method domains → adaugă
   `kiraimobiliare.ro` (Stripe verifică automat că domeniul e al tău).

---

## PARTEA 8 — Google login (opțional) (10 min)  █ TU

1. console.cloud.google.com → creează proiect → "APIs & Services" → "OAuth consent
   screen" → External → completează minim (nume app, email).
2. "Credentials" → Create credentials → **OAuth client ID** → Web application.
   - Authorized JavaScript origins: `https://kiraimobiliare.ro`
3. Copiază **Client ID** (`...apps.googleusercontent.com`) → `.env`
   `RS_GOOGLE_CLIENT_ID` → `systemctl restart kira-api`.
4. Butonul Google apare automat pe `/cont`.

---

## PARTEA 9 — Mentenanță

```bash
# update cod după ce mai lucrăm:
cd /srv/kira && git pull
cd backend && ./.venv/bin/pip install -e .          # dacă s-au schimbat deps
cd ../frontend && npm ci && npm run build           # dacă s-a schimbat frontend
systemctl restart kira-api kira-worker

# loguri live:
journalctl -u kira-api -f
journalctl -u kira-worker -f

# metrici (anunțuri active, prospețime surse, abonați):
curl -s -H "X-Admin-Token: <RS_ADMIN_TOKEN>" https://kiraimobiliare.ro/api/admin/stats

# backup zilnic DB (cron):
crontab -e
# adaugă linia:
0 4 * * * sqlite3 /srv/kira/backend/var/rentscalper.db ".backup /root/rs-backup-$(date +\%F).db"
```

Monitorizare uptime gratis: înregistrează `https://kiraimobiliare.ro/api/health` la
**uptimerobot.com** → primești email dacă pică.

---

## Dacă vrei să-mi dai mie acces (MCP / SSH)

Pentru deploy NU e necesar — varianta "tu rulezi, eu dictez" e mai sigură. Dacă vrei
mentenanță continuă prin mine după lansare, opțiuni:
- îmi dai output-ul comenzilor în chat (cu prefix `!`) și eu îți dau următoarea;
- sau, mai târziu, un MCP SSH server — discutăm atunci, cu cheie dedicată + user
  limitat (nu root), ca să fie sigur.
