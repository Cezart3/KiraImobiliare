# Site Research — Local/Regional Rental Listing Sites (Beyond National Sites)

Research date: 2026-06-12. Covers cities: Cluj-Napoca, Oradea, Timisoara, Iasi, Targu Mures, Bucuresti.

Already-covered national sites (NOT re-evaluated): olx.ro, storia.ro, imobiliare.ro, publi24.ro, capitalimobiliare.ro (Cluj agency).

All probes used `GET` with a Chrome desktop User-Agent + `Accept-Language: ro-RO,ro;q=0.9`, no JS execution. "data access" describes what a plain GET returns.

---

## Cluj-Napoca

| site | rental search URL pattern | data access | anti-bot | difficulty | recommended | notes |
|---|---|---|---|---|---|---|
| piata-az.ro | `https://www.piata-az.ro/imobiliare/apartamente-de-inchiriat/cluj-napoca` (+ `/<neighborhood>`, `/1-camera`, `/2-camere`, etc.) | html-cards | none | easy | yes | Local Cluj classifieds. Cards: `div.announcement[data-id]` with `.announcement__description__title`, `.announcement__info__price > strong` (amount) + `<b>euro</b>`. Sort by `price_eur`. Filter form has `price_from`/`price_to` GET params. Detail link e.g. `/apartament-inchiriat-3-camere-cluj-napoca-buna-ziua-926332`. ~700+ rental ads for Cluj. |
| vdi.ro | `https://www.vdi.ro/apartamente-de-inchiriat/cluj-napoca` (+ `/<neighborhood>`) | html-cards | none | easy | yes | Server-rendered cards `div.mdc-card.property-item.oferta.list-item`, microdata `itemprop="price"` / `itemprop="priceCurrency"` (e.g. `690` / `EUR`), detail link `apartament-...-353248.html`. Price filter inputs `txtPrice` (min) / `txtPrice1` (max), likely posted via form/AJAX — not confirmed as simple GET params. National portal, also covers Bucuresti/Iasi/Timisoara/Oradea/Targu Mures (see National Extras). |
| edil.ro | `https://www.edil.ro/inchirieri-apartamente-19?cauta=Menu&tr=chirie&imob=apartamente` (city implied Cluj-Napoca; agency-specific) | html-cards | none | medium | yes | Single Cluj agency (Edil Imobiliare). Cards `div.listing-item` with `span.listing-price` (e.g. `750 EURO`), detail link `apartamente-inchiriat-2-camere-cluj-napoca-manastur-354974`. 12 cards on first page. Smaller volume but clean markup and agency-exclusive listings not on national portals. |
| compariimobiliare.ro | `https://compariimobiliare.ro/apartamente-de-inchiriat/cluj-napoca` | html-cards (+ld+json/schema microdata) | Cloudflare Rocket Loader present but content renders fully (200, ~810KB real HTML) | easy | yes (see National Extras) | True multi-agency aggregator. 20 cards/page, `div.search-card.search-result.property-result` with full `schema.org/Offer` microdata (`itemprop="price"`, `priceCurrency`, `seller.name`). Listed here for completeness; full eval in National Extras since it covers all 6 cities. |

---

## Oradea

| site | rental search URL pattern | data access | anti-bot | difficulty | recommended | notes |
|---|---|---|---|---|---|---|
| upimobiliare.ro | `https://www.upimobiliare.ro/inchirieri-apartamente/oradea-2887/1` (trailing `/1` = page number; `/<neighborhood-slug>-<id>/1` for areas, e.g. `/dacia-1759/1`) | html-cards | none | easy | yes | Single Oradea agency (UP Imobiliare), but appears to be the most active local agency portal for Oradea rentals. Cards `div.item-grid__container > div.listing`, `p.listing__price` (e.g. `350 EUR`), `h3.listing__title`, detail link `apartament-2-camere-de-inchiriat-decebal-oradea-647.html`. 11 cards on first page. No price-range GET param found (likely UI-only). |
| vdi.ro | `https://www.vdi.ro/apartamente-de-inchiriat/oradea` | html-cards | none | easy | yes | Same structure as verified for Cluj (see National Extras / Cluj row). Confirmed to have an Oradea-specific listings URL via search results. |
| compariimobiliare.ro | `https://compariimobiliare.ro/apartamente-de-inchiriat/oradea` | html-cards + schema microdata | Rocket Loader only, content renders | easy | yes (National Extras) | Multi-agency aggregator confirmed for Oradea/Bihor via search results ("toate ofertele... din Bihor"). |

Note: no independent Oradea classifieds/portal beyond OLX/Storia/Publi24/VDI/UP Imobiliare was found with meaningful volume; `easyimobiliare.ro` (verified, see Targu Mures) does not appear to list Oradea.

---

## Timisoara

| site | rental search URL pattern | data access | anti-bot | difficulty | recommended | notes |
|---|---|---|---|---|---|---|
| imopuls.ro | `https://www.imopuls.ro/inchirieri-apartamente-timisoara` | html-cards (+per-card ld+json `Product`) | none | easy | yes | Single Timisoara agency (ImoPuls), ~93 rental listings, daily-updated per their copy. Cards `div.box-anunt` with `h3` price text `550 €/lună`, detail link `/detalii/apartament-de-inchiriat-2-camere-55mp-zona-p-ta-victoriei-timisoara/3167251`, plus a per-listing `<script type="application/ld+json">` with `@type: "Product"`. 21 cards on first page, pagination present (no clean price filter param found). |
| vdi.ro | `https://www.vdi.ro/apartamente-de-inchiriat/timisoara` | html-cards | none | easy | yes | Same structure as verified for Cluj (see National Extras). Confirmed Timisoara URL exists via search results. |
| compariimobiliare.ro | `https://compariimobiliare.ro/apartamente-de-inchiriat/timisoara` | html-cards + schema microdata | Rocket Loader only, content renders | easy | yes (National Extras) | Multi-agency aggregator, confirmed for Timis county. |
| timisoreni.ro | `https://www.timisoreni.ro/info/apartamente/with--inchiriere_3/` | BLOCKED | **Cloudflare JS challenge** (`Just a moment...`, 403) | blocked | no | Local classifieds, only ~54 rental listings anyway — low value even if unblocked. |

---

## Iasi

| site | rental search URL pattern | data access | anti-bot | difficulty | recommended | notes |
|---|---|---|---|---|---|---|
| interimobiliare.ro | `https://interimobiliare.ro/apartamente-de-inchiriat-iasi` (pagination `?p=2`..`?p=5`; sub-paths for rooms/areas e.g. `/1-camera`, `/centru`) | html-cards | none | easy | yes | Single Iasi agency/portal, 109 active rental listings (largest single-source count found for Iasi). Cards `div.offer.flex.wrap.fspace` with `span.price.no-mobile` (e.g. `650 EURO`), detail link with numeric "Cod oferta". 25 cards/page, 5 pages. No price GET param found, but neighborhood/room sub-paths exist. |
| vdi.ro | `https://www.vdi.ro/apartamente-de-inchiriat/iasi` | html-cards | none | easy | yes | Same structure as Cluj (see National Extras). Confirmed Iasi URL via search results. |
| compariimobiliare.ro | `https://compariimobiliare.ro/apartamente-de-inchiriat/iasi` | html-cards + schema microdata | Rocket Loader only, content renders | easy | yes (National Extras) | Multi-agency aggregator, confirmed for Iasi (also has `/garsoniere-de-inchiriat/iasi`, `/case-vile-de-inchiriat/iasi`). |
| evo-imobiliare.ro | `https://www.evo-imobiliare.ro/inchirieri-apartamente` | not probed | not probed | n/a | no (unverified) | Search snippet claims "100+ daily-updated rental offers in Iasi county". Not fetched due to fetch budget; lower priority than interimobiliare.ro which was directly verified with a larger count. |

---

## Targu Mures

| site | rental search URL pattern | data access | anti-bot | difficulty | recommended | notes |
|---|---|---|---|---|---|---|
| fayoraimobiliare.ro | `https://www.fayoraimobiliare.ro/inchirieri-apartamente/targu-mures-1/1` (trailing `/1` = page) | html-cards | none | easy | yes | Single Targu Mures agency (Fayora Imobiliare). Cards `article.property-item.clearfix`, price `h5.price` (e.g. `420 € pe luna`), detail link `apartament-2-camere-de-inchiriat-libertatii-targu-mures-6450.html`. 9 cards on first page. |
| vdi.ro | `https://www.vdi.ro/apartamente-de-inchiriat/targu-mures` | html-cards | none | easy | yes | Same structure as Cluj (see National Extras). Confirmed Targu Mures URL via search results. |
| compariimobiliare.ro | `https://compariimobiliare.ro/apartamente-de-inchiriat/targu-mures` (+ `/pagina-2`...`/pagina-5`, neighborhood sub-paths e.g. `/unirii`, `/dambu-pietros`, `/7-noiembrie`) | html-cards + schema microdata | Rocket Loader only, content renders | easy | yes (National Extras) | Multi-agency aggregator with at least 5 pages (~100+ listings) for Targu Mures — best volume found for this city among local/regional sources. |
| easyimobiliare.ro | `https://www.easyimobiliare.ro/inchirieri-apartamente/targu-mures-9484/1` | html-cards (WordPress/gdlr theme, schema.org `Offer` itemscope) | none | easy | no | Verified live and structurally clean (`div.gdlr-core-portfolio-item`, `div.property_meta_price` with `itemprop="price"`/`currency`), but only **1 listing** found on first page — too low volume to be worth implementing. |

---

## Bucuresti

| site | rental search URL pattern | data access | anti-bot | difficulty | recommended | notes |
|---|---|---|---|---|---|---|
| romimo.ro | `https://www.romimo.ro/apartamente/inchiriere/bucuresti/` (also `/apartamente/inchiriere/<county>/<city>/` for all cities, area filter `?area=<slug>`) | html-cards + ld+json `ItemList` | none | easy | conditional | Server-rendered `div.article-item[data-articleid]` cards inside `div.searchresult` / `div.rmd-container-search-results`. **However**, listing images are served from `s3.publi24.ro` and detail URLs are `romimo.ro/anunturi/imobiliare/de-inchiriat/apartamente/.../anunt/...html` — strong evidence romimo.ro shares the same Ringier/Publi24 listing pool as **publi24.ro** (already covered). Likely high overlap; only worth adding if dedup against publi24.ro is implemented, or if romimo's ld+json `ItemList` (with full `description`/`price`/`url` per item) proves easier to parse than publi24's own pages. |
| vdi.ro | `https://www.vdi.ro/imobiliare-bucuresti` / `https://www.vdi.ro/apartamente-de-inchiriat/bucuresti` | html-cards | none | easy | yes | Same structure as verified for Cluj (see National Extras). Independent listing pool (not obviously tied to publi24/OLX based on Cluj probe). |
| compariimobiliare.ro | `https://compariimobiliare.ro/apartamente-de-inchiriat/bucuresti` | html-cards + schema microdata | Rocket Loader only, content renders | easy | yes (National Extras) | Multi-agency aggregator confirmed for Bucuresti. Given Bucuresti's huge market, likely the highest-volume of the non-national sites for this city. |
| imo24.ro | `https://imo24.ro/inchirieri-apartamente/bucuresti` (city slug; Cluj probed as `/inchirieri-apartamente/cluj`) | html-cards (initial load) + AJAX filter API | none | medium | conditional (National Extras) | See National Extras — works but only ~20 cards rendered server-side per probe; full result set likely behind AJAX (`pret_min`/`pret_max` params visible in filter form). |
| anuntul.ro | — | NOT FOUND as a real-estate site | n/a | n/a | no | Could not locate an active `anuntul.ro` real-estate rentals section via search; results for "anuntul.ro" queries returned only Storia/other sites. Likely defunct, redirected, or not a meaningful rental source. Do not implement. |

---

## NATIONAL EXTRAS (cover all 6 target cities)

| site | rental search URL pattern | data access | anti-bot | difficulty | recommended | notes |
|---|---|---|---|---|---|---|
| vdi.ro | `https://www.vdi.ro/apartamente-de-inchiriat/<city-slug>` (e.g. `cluj-napoca`, `bucuresti`, `iasi`, `timisoara`, `targu-mures`, `oradea`); neighborhood sub-paths also exist (e.g. `/cluj-napoca/manastur`-style observed in nav) | html-cards | none | easy | **yes** | Verified in depth on Cluj-Napoca probe: clean server-rendered `div.mdc-card.property-item.oferta.list-item` cards, `h3.price` with `<span itemprop="price">690</span>` / `<span itemprop="priceCurrency">EUR</span>`, detail links `apartament-...-<numericid>.html`. No Cloudflare/anti-bot. City URLs for all 6 target cities confirmed to exist via WebSearch (vdi.ro/apartamente-de-inchiriat/{oradea,timisoara,iasi,targu-mures,bucuresti} all returned by search). Price filter inputs (`txtPrice`/`txtPrice1`) exist but likely require POST/AJAX — start with plain listing pages, add price filtering later if a GET-param pattern is found by testing live. **Top overall pick.** |
| compariimobiliare.ro | `https://compariimobiliare.ro/apartamente-de-inchiriat/<city-slug>` (e.g. `cluj-napoca`, `bucuresti`, `oradea`, `timisoara`, `iasi`, `targu-mures`); pagination `/pagina-N`; neighborhood sub-paths e.g. `/targu-mures/unirii`; rooms sub-paths e.g. `/1-camere`; price filter param `pPrice` (also `price_selector` field present in UI) | html-cards + full schema.org `Offer` microdata | Cloudflare Rocket Loader script present (`window.__cfRLUnblockHandlers` checks in onclick handlers) but **does not block** — page returns 200 with ~810KB of real HTML/listings | easy | **yes** | True cross-agency aggregator — verified cards show different seller agency names per listing (`itemprop="seller"` → e.g. "Sigma Imobiliare"), confirming real multi-source data, not a single agency's site. 20 cards/page verified for Cluj-Napoca; confirmed via search to have 5+ pages for Targu Mures alone. Each card: `div.search-card.search-result.property-result` with `<meta itemprop="price" content="350"/>`, `<meta itemprop="priceCurrency" content="EUR"/>`, `<meta itemprop="availability".../>`. **Strong #2 overall pick** — likely the best single new source for incremental listings not on OLX/Storia/Imobiliare/Publi24. |
| imo24.ro | `https://imo24.ro/inchirieri-apartamente/<city-slug>` (e.g. `cluj`, `bucuresti`) | html-cards (initial render ~20 items) + AJAX-driven filtering (`pret_min`/`pret_max` params present in filter form, but full result set appears to load via JS/AJAX rather than URL query) | none on initial GET | medium | conditional | Verified for Cluj: 20 real cards server-rendered (`div.listare_boxa.listare_anunt_<id>`, price text e.g. `500 €`), `total_rez` shows `"20 anunturi"` — unclear if that's the full count or a default page size, since filtering UI is AJAX (`$('#anunturi_in')`). Worth a follow-up probe with `pret_min`/`pret_max` as GET params before committing engineering time; if AJAX-only, treat as medium/skip. |
| lajumate.ro | `https://lajumate.ro/anunturi/imobiliare/apartamente-de-inchiriat/in/<county-slug>/<city-slug>` (e.g. `/in/cluj/cluj-napoca`); price filter via `?price_max=<value>` query param (and presumably `price_min`) | **next-data** (`<script id="__NEXT_DATA__">` → `props.pageProps.adsServer`: array of objects with `id`, `title`, `price`, `currency`, `city`, `images`, `listed_at`, `user.phone`) + `props.pageProps.paginationServer` (`currentPage`/`totalPages`/`totalAds`/`adsPerPage`) | none | easy | **yes** | Cleanest structured-data source found in this research. Verified Cluj-Napoca: **1,188 total rental ads**, 43 pages of 28. `price_max` query param confirmed to be reflected in `selectedFiltersServer` (filter mechanism works, though `price_max=500` returned 0 results for Cluj — likely just too low for that market, not a broken filter). Each ad object includes phone number, listing date, full image paths — minimal extra parsing needed vs HTML scraping. **Strong #3 overall pick / arguably tied for #1 given data quality.** |
| romimo.ro | `https://www.romimo.ro/apartamente/inchiriere/<county>/<city>/` (e.g. `/cluj/cluj-napoca/`, `/bucuresti/` — note Bucuresti uses a shorter path without county segment per search results) | html-cards (`div.article-item[data-articleid]`) + `<script type="application/ld+json">` `ItemList` with per-item `name`/`description`/`price`(embedded in description text)/`url` | none | easy | **no (likely redundant with publi24.ro)** | Technically easy and well-structured, but listing images point to `s3.publi24.ro` CDN and detail-page URL scheme (`/anunturi/imobiliare/de-inchiriat/apartamente/.../anunt/<hash>.html`) strongly suggests romimo.ro is a front-end over the same Ringier Romania / Publi24 listing inventory already covered by publi24.ro. Recommend skipping unless a quick manual comparison shows distinct listings. |

---

## TOP PICKS

Ordered by value (listing volume × ease of integration):

### National (implement first — covers all 6 cities with one integration each)
1. **lajumate.ro** — `__NEXT_DATA__` JSON with `adsServer` array (id, title, price, currency, city, images, phone, date). 1,188 ads for Cluj-Napoca alone. `price_max`/`price_min` query params. No anti-bot. URL: `lajumate.ro/anunturi/imobiliare/apartamente-de-inchiriat/in/<county>/<city>`.
2. **compariimobiliare.ro** — true cross-agency aggregator, schema.org `Offer` microdata per card, 20/page with pagination, `pPrice` filter param. URL: `compariimobiliare.ro/apartamente-de-inchiriat/<city-slug>`.
3. **vdi.ro** — clean server-rendered cards with `itemprop="price"`/`priceCurrency` microdata, confirmed URLs for all 6 cities, no anti-bot. URL: `vdi.ro/apartamente-de-inchiriat/<city-slug>`.

### Cluj-Napoca
1. **piata-az.ro** — Cluj-focused classifieds, `price_from`/`price_to` GET params, ~700+ ads, clean `.announcement` cards.
2. **edil.ro** — local agency, exclusive listings, `.listing-item` cards with `.listing-price`.
(vdi.ro / compariimobiliare.ro / lajumate.ro already cover Cluj as National picks.)

### Oradea
1. **upimobiliare.ro** — most active local Oradea agency portal, `.item-grid__container/.listing` cards with `.listing__price`.
(vdi.ro / compariimobiliare.ro / lajumate.ro cover Oradea as National picks.)

### Timisoara
1. **imopuls.ro** — local agency, ~93 rentals, `.box-anunt` cards + per-listing ld+json `Product`.
(vdi.ro / compariimobiliare.ro / lajumate.ro cover Timisoara as National picks.)

### Iasi
1. **interimobiliare.ro** — largest single-source count found (109 active), `.offer.flex.wrap.fspace` cards, 5 pages of 25.
(vdi.ro / compariimobiliare.ro / lajumate.ro cover Iasi as National picks.)

### Targu Mures
1. **compariimobiliare.ro** — best volume for this smaller city (5+ pages, ~100+ ads), already a National pick.
2. **fayoraimobiliare.ro** — local agency, `.property-item` cards, `h5.price`, 9/page.
(easyimobiliare.ro rejected: only 1 listing found.)

### Bucuresti
1. **compariimobiliare.ro** — likely highest-volume non-national source given Bucuresti's market size; already a National pick.
2. **vdi.ro** — independent listing pool, already a National pick.
3. romimo.ro — NOT recommended (likely duplicate of publi24.ro inventory via shared Ringier/S3 infrastructure).

### Rejected / Blocked
- **timisoreni.ro** — blocked by Cloudflare JS challenge (403 "Just a moment...").
- **anuntul.ro** — could not locate as an active real-estate rentals site.
- **easyimobiliare.ro** (Targu Mures) — only 1 rental listing found, too low volume.
- **imo24.ro** — works on initial GET (20 cards/city) but filtering appears AJAX-driven; revisit if `pret_min`/`pret_max` GET params are confirmed to work server-side.
- **romimo.ro** — likely redundant with publi24.ro (shared image CDN `s3.publi24.ro` and URL scheme).
