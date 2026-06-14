<div align="right"><a href="README.md">🇬🇧 English</a></div>

# Kira — caută chirii din toată România, local pe calculatorul tău

**Kira** adună anunțurile de chirii de pe mai multe site-uri (Storia, OLX, Imobiliare,
Publi24, Lajumate și altele) într-un singur loc, cu filtre pe care site-urile sursă
nu le au:

- **centrală proprie vs termoficare** (le separă automat din textul anunțului)
- **parcare inclusă** sau **loc de parcare de închiriat în apropiere** (cu distanță pe jos)
- **distanța de la o adresă a ta** (ex: facultatea) până la fiecare chirie + link Google Maps

Rulează **100% local, gratuit, fără cont, fără plată.** Datele rămân pe calculatorul
tău. Fiecare card te trimite la anunțul original de pe site-ul sursă.

> 🐶 **De ce „Kira"?** E numele cățelușei mele — partenera mea de frustrare în lunile
> în care căutam o chirie jonglând cu 6 site-uri deschise în paralel. Tool-ul ăsta
> rezolvă fix bătaia de cap prin care am trecut împreună, așa că îi poartă numele.

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

## Cum îl pornești — ghid complet pentru ORICINE (chiar dacă n-ai mai folosit un terminal)

Pare mult, dar e doar copy-paste. Durează ~15 minute prima dată. Urmează în ordine,
nu sări pași. Ghidul e pentru **Windows** (jos ai și notele pentru Mac/Linux).

### Pasul 0 — Instalează cele 3 programe gratuite (o singură dată)

Ai nevoie de trei programe. Le descarci gratis, dai next-next-install la toate:

1. **Python** (motorul aplicației)
   - Mergi la 👉 https://www.python.org/downloads/
   - Apasă butonul galben mare „Download Python".
   - Deschide fișierul descărcat. **FOARTE IMPORTANT:** în prima fereastră,
     bifează căsuța **„Add python.exe to PATH"** (jos), apoi apasă „Install Now".
   - (Dacă uiți să bifezi, dezinstalează și reia — altfel nu merge.)

2. **Node.js** (pentru interfața din browser)
   - Mergi la 👉 https://nodejs.org/
   - Apasă butonul mare „LTS" (versiunea recomandată). Deschide fișierul, next-next-install.

3. **Git** (ca să descarci proiectul)
   - Mergi la 👉 https://git-scm.com/downloads
   - Alege Windows, descarcă, next-next-install (lasă toate setările implicite).

După ce le-ai instalat pe toate trei, **repornește calculatorul** (ca să le „vadă" sistemul).

### Pasul 1 — Deschide un terminal

Un „terminal" e o fereastră unde scrii comenzi. Pe Windows:
- Apasă tasta **Windows**, scrie **`powershell`**, apasă Enter.
- Se deschide o fereastră albastră/neagră. Acolo lipești comenzile de mai jos.
- Ca să **lipești** în terminal: click dreapta (sau Ctrl+V).

### Pasul 2 — Descarcă proiectul

Lipește asta în terminal și apasă Enter (descarcă proiectul în folderul tău):
```
git clone https://github.com/Cezart3/KiraImobiliare.git
cd KiraImobiliare
```

### Pasul 3 — Pornește „creierul" aplicației (backend)

Lipește pe rând (Enter după fiecare bloc). Prima comandă pregătește, a doua instalează
(durează 1-2 min), a treia pornește:
```
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```
Când vezi un mesaj cu „Uvicorn running on http://127.0.0.1:8000" — **merge!**
⚠️ **Lasă această fereastră deschisă** (dacă o închizi, aplicația se oprește).

### Pasul 4 — Pornește interfața (al doilea terminal)

Deschide un **AL DOILEA** terminal (repetă Pasul 1 — încă o fereastră PowerShell).
Lipește:
```
cd KiraImobiliare\frontend
npm install
npm run dev
```
`npm install` durează 1-2 min prima dată. Când vezi „Local: http://localhost:5173" —
gata! Lasă și fereastra asta deschisă.

### Pasul 5 — Folosește aplicația

Deschide în browser (Chrome, Edge, etc.): **http://localhost:5173**

Alege orașul → apasă **„Actualizează anunțuri"**. Prima dată durează ~10–12 minute
(aduce TOATE anunțurile de la 6 surse — vezi progresul live pe ecran, nu e blocat,
doar lucrează); după aceea totul e instant. Apeși „Actualizează" oricând vrei anunțuri
proaspete. Gata — caută în voie! 🎉

### Cum o pornești data viitoare

Nu mai reinstalezi nimic. Doar deschizi 2 terminale și rulezi:
- Terminal 1: `cd KiraImobiliare\backend` apoi `.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000`
- Terminal 2: `cd KiraImobiliare\frontend` apoi `npm run dev`
- Deschizi http://localhost:5173

### Cum o oprești
În fiecare terminal apasă **Ctrl+C** (sau pur și simplu închide ferestrele).

### Pe Mac sau Linux?
La fel, doar că:
- Python/Node/Git le instalezi de pe aceleași site-uri (sau cu `brew` pe Mac).
- La Pasul 3 folosește `.venv/bin/python` în loc de `.venv\Scripts\python.exe`
  (de ex. `.venv/bin/pip install -e .` și `.venv/bin/python -m uvicorn app.main:app --port 8000`).

### Ceva nu merge?
- **„python nu este recunoscut"** → n-ai bifat „Add to PATH" la instalare; reinstalează Python cu căsuța bifată, apoi repornește calculatorul.
- **Eroare la `python -m venv .venv`** (mesaj cu `venvlauncher.exe` / „Unable to copy") → ai **Anaconda** instalat și e activ (vezi `(base)` la începutul liniei din terminal). Scrie întâi `conda deactivate`, apoi reia de la `python -m venv .venv`. (Sau folosește Python „normal" de pe python.org, nu cel din Anaconda.)
- **„address already in use" / `Errno 10048` pe portul 8000** → ai deja ceva pornit pe acel port (de obicei o rulare veche a aplicației, lăsată deschisă). Cel mai simplu: închide acea fereastră veche de terminal și reia Pasul 3. (Pe Windows, dacă nu o găsești, repornește calculatorul — eliberează portul sigur.)
- Tot blocat? Scrie-mi: cezartocaciu233@gmail.com — te ajut.

> Opțional (avansat): copiază `.env.example` în `.env` dacă vrei să ajustezi viteza de
> scraping etc. Nu e necesar — merge cu valorile implicite.

---

## Ce poate face

- căutare + filtre (preț, camere, zonă, încălzire, parcare, sursă)
- sortare, inclusiv **după distanța** față de adresa ta
- **favorite** + **comparare** între anunțuri (salvate local, în browserul tău)
- „cea mai bună alegere din favorite" (scor pe preț, distanță, parcare, încălzire)
- mod întunecat

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
