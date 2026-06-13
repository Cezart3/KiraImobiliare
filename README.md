# Kira — caută chirii din toată România, local pe calculatorul tău

**Kira** adună anunțurile de chirii de pe mai multe site-uri (Storia, OLX, Imobiliare,
Publi24, Lajumate și altele) într-un singur loc, cu filtre pe care site-urile sursă
nu le au:

- **centrală proprie vs termoficare** (le separă automat din textul anunțului)
- **parcare inclusă** sau **loc de parcare de închiriat în apropiere** (cu distanță pe jos)
- **distanța de la o adresă a ta** (ex: facultatea) până la fiecare chirie + link Google Maps

Rulează **100% local, gratuit, fără cont, fără plată.** Datele rămân pe calculatorul
tău. Fiecare card te trimite la anunțul original de pe site-ul sursă.

> Gândit pentru studenți din centrele universitare: Cluj-Napoca, București, Timișoara,
> Iași, Oradea, Târgu Mureș.

> 💚 **Folosește-l liber, local — și spune prietenilor!** Te încurajez să-l clonezi,
> să-l rulezi pe calculatorul tău și să-l recomanzi colegilor. Singura limită:
> rămâne **strict local** — nu îl republica pe alt repo, nu-l găzdui public și nu
> face bani din el. Vezi [Licență](#licență) pentru motivul legal.

<p align="center">
  <img src="docs/screenshots/home-light.png" width="49%" alt="Listă anunțuri — light" />
  <img src="docs/screenshots/home-dark.png" width="49%" alt="Listă anunțuri — dark" />
</p>

---

## Cum îl pornești (pas cu pas, pentru oricine)

Ai nevoie o singură dată de: **Python 3.12+** și **Node.js 20+** (le instalezi gratis
de pe python.org și nodejs.org).

### 1. Descarcă proiectul
```bash
git clone https://github.com/Cezart3/KiraImobiliare.git
cd KiraImobiliare
```

### 2. Pornește backend-ul (un terminal)
```bash
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .      # Windows
# pe Mac/Linux:  .venv/bin/pip install -e .
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

### 3. Pornește interfața (al doilea terminal)
```bash
cd frontend
npm install
npm run dev
```

### 4. Deschide în browser
**http://localhost:5173** — alege orașul, apasă **„Actualizează anunțuri"** și gata.
Prima actualizare durează câteva minute (aduce anunțuri de la 6 surse); după aceea
totul e instant. Apeși „Actualizează" oricând vrei anunțuri proaspete.

> Opțional: copiază `.env.example` în `.env` dacă vrei să ajustezi viteza de scraping,
> bugetul de geocodare etc. Nu e obligatoriu — aplicația merge cu valorile implicite.

---

## Ce poate face

- căutare + filtre (preț, camere, zonă, încălzire, parcare, sursă)
- sortare, inclusiv **după distanța** față de adresa ta
- **favorite** + **comparare** între anunțuri (salvate local, în browserul tău)
- „cea mai bună alegere din favorite" (scor pe preț, distanță, parcare, încălzire)
- mod întunecat

## Pentru dezvoltatori (opțional)

Dacă vrei să rulezi testele sau să modifici codul:
```bash
cd backend
.venv/Scripts/python.exe -m pip install -e ".[dev]"   # instalează și pytest, ruff
.venv/Scripts/python.exe -m pytest -q                 # 70 teste
.venv/Scripts/ruff.exe check app
```

## Cum funcționează (pe scurt)

Un worker descarcă politicos paginile publice de anunțuri → un pipeline cu regex
extrage din textul românesc faptele (încălzire, parcare, preț, cameră, stradă) →
totul se geocodează și se potrivește cu locuri de parcare din apropiere → API-ul
(FastAPI) servește, iar interfața (React) afișează.

```
backend/   Python 3.12 · FastAPI · SQLAlchemy · APScheduler · SQLite
frontend/  React 18 · TypeScript · Tailwind v4 · TanStack Query
```

## În lucru / viitor

Dacă proiectul prinde, urmează **anunțuri de vânzare imobiliare** (nu doar chirii) și
mai multe orașe. **Ai idei sau ai găsit un bug?** Deschide un *issue* pe GitHub sau
scrie la cezartocaciu233@gmail.com — chiar citesc fiecare mesaj. Un ⭐ pe repo ajută.

## De ce „Kira"?

Kira e cățelușa mea 🐶 — partenera mea de frustrare în lunile în care căutam o chirie
și jonglam cu 6 site-uri deschise în paralel. Tool-ul ăsta rezolvă fix bătaia de cap
prin care am trecut împreună. Așa că i-am pus numele ei.

## Notă legală

Proiect personal/educațional, pentru **uz local și personal**. Scraping politicos
(delay-uri, cap de pagini, cache); datele rămân la sursă — fiecare card trimite la
anunțul original. **Dacă rulezi aplicația, ești responsabil să respecți Termenii și
Condițiile fiecărui site sursă.** Nu se stochează date de contact din anunțuri, iar
**acest depozit nu conține niciun anunț** — fiecare utilizator își generează singur
datele, local, la prima rulare.

## Licență

**Licență de utilizare personală (source-available, proprietar).** Vezi fișierul
[LICENSE](LICENSE). Pe scurt:

- ✅ **Poți** (ești încurajat!): să-l clonezi, să-l rulezi/modifici **local, pentru tine**,
  gratuit, și să-l recomanzi prietenilor să facă la fel.
- ❌ **Nu poți**: să-l redistribui/republici pe alt repo, să-l găzduiești public,
  să oferi un serviciu din el sau să faci bani din el.

**De ce nu e permisă publicarea/monetizarea:** aplicația agregă anunțuri de pe site-uri
terțe (OLX, Storia etc.), ai căror Termeni și Condiții **interzic** preluarea, agregarea
și reutilizarea comercială a datelor. Rularea **locală, personală** (fiecare pentru el)
este utilizare privată și mult mai apărabilă; însă a publica un serviciu public sau a
face bani din datele lor ar încălca acei termeni și legislația privind bazele de date.
De aceea: **use local = ok; publicare/comercial = nu.**

Drepturile de autor asupra codului aparțin autorului. © 2026 Cezar Tocaciu — toate
drepturile rezervate. Pentru orice altă utilizare, scrie la cezartocaciu233@gmail.com.

---

<sub>Autor: Cezar Tocaciu · [LinkedIn](https://www.linkedin.com/in/tocaciu-cezar-0865373b6/)</sub>
