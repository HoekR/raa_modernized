# Legacy UX — Huygens RAA search model

Reference for parity work against the live Huygens UI and the original Zope/SQLObject app in `RepertoriumAmbtenarenAmbtsdragers`.

- Zoekhulp (overview): https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/zoekhulp
- Field help (in-app `?` tooltips): https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/app/help
- Legacy source: `src/raa/browser/templates/`, `query.py`, `form.py`

**Pilot note:** Huygens detail URLs (`/app/personen/{id}`) use **legacy** primary keys. The modern pilot uses import IDs from `extab.pkl` — they do not match. For parity checks on a named example, use the concordance in [MIGRATION_LOG.md](MIGRATION_LOG.md) (e.g. Tjaerd baron van Aylva: legacy 6448 → pilot 21009).

## Entry points

| Screen | Perspective | Result unit |
|--------|-------------|-------------|
| **Personen zoeken** | Person and career | One row per **persoon** (name + life years) |
| **Aanstellingen zoeken** | Institution | One row per **aanstelling**, grouped instelling → functie |
| **Instellingen** | Institution browse | A–Z list; ≤5 hits can jump to aanstellingen search |
| **Functies** | Function browse | Same pattern as instellingen |

## Personen vs aanstellingen

Both screens share office-related filters (functie, instelling, vertegenwoordiging, stand; aanstellingen also has adel). They differ in **which fields exist** and **how results are shown**.

### Personen zoeken

- **Identity:** geslachtsnaam, voornaam, naamsvariant (alias), heerlijkheid, opmerkingen
- **Status:** adel, titels (adellijk + academisch)
- **Dates:** geboorte, overlijden, aanstellingsdatum (each an open-ended range)
- **Office:** functie, instelling (multi-select, **en/of**), vertegenwoordiging, stand
- **Results:** flat list; click name → person detail
- **Sort:** voornaam, geslachtsnaam, geboortedatum, overlijdensdatum

Office and geo filters are evaluated via **linked aanstellingen** (`query.py` joins `Persoon` ↔ `Aanstelling`).

### Aanstellingen zoeken

- **No** person-identity fields on the form (no naam/alias/titels)
- **Periode:** zittingstermijn on the appointment (`van` / `tot`), not historical period flags
- **Office:** functie, instelling (multi-select, **en/of**)
- **Vertegenwoordiging, stand, adel:** same as personen
- **Results:** nested list instelling → functie → person (van – tot); toggle group by instelling or functie
- **Sort:** default instelling.naam → functie.naam → `van`; also voornaam, geslachtsnaam, life dates

### Pagination

Both: **100 results per page**, vorige/volgende, sort links (↑↓).

## Vertegenwoordiging

Zoekhulp: choose a **provincie/departement**, **regio**, or **plaats/grietenij/kiesdistrict**. Whether a given institution uses geographic representation is explained in its **institutionele toelichting**.

### Search UI (legacy)

Three parallel multi-select columns under one heading:

| UI label | DB table | FK on `aanstelling` |
|----------|----------|---------------------|
| provinciaal | `provincie` | `provincie_id` |
| regionaal | `regio` | `regio_id` |
| lokaal | `lokaal` | `lokaal_id` |

- Multiple values in one column = **OR** (`IN (...)`)
- Filters in different columns combine with **AND** (appointment must match each active column)
- **`gewest_id`** exists on some appointments but has **no** legacy search column
- **`vertegenwoordigend`** is **not** a search field; it splits **person detail** display (see below)

### Modern pilot (slice 1)

- API: `filters.provincie_id`, `filters.regio_id`, `filters.lokaal_id` (lists of integer IDs)
- UI: three typeahead + chip multi-selects on personen and aanstellingen
- Suggest: `/api/suggest/{provincie,regio,lokaal}` scoped by period via `aanstelling` join

## Person detail — bovenlokaal vs vertegenwoordigend

On the person page (`persoon.pt`), appointments are split by `aanstelling.vertegenwoordigend`:

| Flag | Section | Meaning |
|------|---------|---------|
| `1` (true) | Short list under life dates | Local/regional **representative** roles |
| `0` (false) | “Functies in bovenlokale instellingen” | Offices in supra-local institutions |

For bovenlokale appointments with geo/stand data, the detail shows:

> **namens:** provincie, regio, lokaal, stand

Each bovenlokale block links to **anderen met deze aanstelling…** (pre-filled aanstellingen search).

**Not yet in pilot:** full personen field set (alias/titels/date ranges as separate filters).

## Functie / instelling en vs of

| Mode | Personen | Aanstellingen |
|------|----------|---------------|
| **of** (default) | Person held **any** selected functie/instelling | Appointment matches **any** selected value |
| **en** | Person held **all** selected values (separate sub-join per item) | Same pattern |

Legacy limits multi-select to **5** items per field.

## Wildcards (text fields)

Legacy `_text_search`: `?` → one char, `*` → sequence; space-separated tokens are **AND**; quoted `"phrase"` is exact-ish match.

## Institution navigation

Click institution name → list of functies within that institution + **institutionele toelichting** (HTML). Functie names link to filtered aanstellingen search.

## Historical period (modernization)

Legacy search forms do **not** expose Republiek / Bataafs-Franse tijd / 19e eeuw as a global dropdown. Our pilot adds a **periode** selector using bitmask columns (`republiek`, `batfra`, `negentiende_eeuw`, `me`, `republiek_friezen`) on imported tables.

`republiek_friezen` is **not** a separate search period: it marks rows that were **separately edited** in `raa_convert` (Fries/Republic track). The UI period **Republiek** includes both `republiek` and `republiek_friezen` rows; the extra column stays in the DB for provenance.

`divperioden` rows are purged on import (superseded by `republiek_friezen`).

## Enhancements above legacy (modern pilot)

Documented in [MIGRATION_LOG](docs/MIGRATION_LOG.md) D-37–D-39. Not in the Huygens zoekhulp UI.

| Feature | Behaviour |
|---------|-----------|
| **No geslachtsnaam** | 51 persons voornaam-only; display/sort without leading comma (D-37) |
| **Shadow life dates** | Infer life span from aanstellingen when birth/death missing; default **included** in range search; radio **“zoek exacte datums”** excludes shadow (D-38) |
| **EDTF life-date search** | Level 1 intervals on personen geboorte/overlijden; aanstellingen stay ISO in v1 (D-39) |

Reference implementation for shadow logic: `~/develop/republic_clean/republic/data/datamangler.py` (`hypothetical_life`, offsets 34/22).

### Entity spans — functie × instelling (B2e)

Import-time auxiliary tables (D-55–D-57). Not in legacy Huygens UI.

| Feature | Behaviour |
|---------|-----------|
| **Corpus first/last** | Per `functie_id`: earliest/latest **dated aanstelling** anywhere in the DB, with witness instelling |
| **Institutional contexts** | Per `(functie_id, instelling_id)`: date span + count; multiple parallel or sequential rows |
| **Labelling** | Never “office created/abolished”; always “vroegste/laatste gedateerde aanstelling in het bestand” |
| **Gaps** | Shown as-is — **not** filled or merged into one ambtsketen (D-57) |
| **Institutional view** | Corpus edited institution-first, but `instelling` rows are not versioned and lack succession FKs; regime change may appear as a new `instelling_id` (D-56 note) |

**UI pointer (required when B2e ships):** short caveat under span stats + link to **institutionele toelichting** on linked instellingen and [zoekhulp — institutionele context](https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/zoekhulp).

## Parity checklist

| Feature | Legacy | Pilot |
|---------|--------|-------|
| Personen naam / alias / titels / dates | ✓ | ✓ (single `q` → `search_display` B2f; detail B2d; aanstellingsdatum B3d) |
| Vertegenwoordiging search | ✓ | ✓ (2026-07-12 — see [MIGRATION_LOG](docs/MIGRATION_LOG.md)) |
| Aanstellingen nested grouping | ✓ | ✓ (2026-07-13 — nested UI; toggle instelling/functie) |
| Person detail bovenlokaal / namens | ✓ | ✓ (2026-07-13) |
| Functie/instelling en/of | ✓ | ✓ (2026-07-13 — chip multi-select + en/of) |
| Instelling → functies → aanstellingen | ✓ | ✓ (2026-07-13 — functie links on instelling detail) |
| Instellingen / functies A–Z browse | ✓ | ✓ (2026-07-17 — B3e) |
| Person detail bronnen / opmerkingen / titels | ✓ | ✓ (2026-07-13 — B2d) |
| Functie / instelling entity profile | basic list | ✓ (2026-07-13 — stats, actions, related links) |
| Functie institutional spans | — | ✓ (2026-07-13 — B2e, D-55–D-57) |
| `republiek_friezen` period option | — | Separate **edit track** in convert; merged into Republiek in search |
| Display name (no geslachtsnaam) | awkward `, voornaam` | ✓ B2a (D-37) |
| Shadow + EDTF life-date search | — | ✓ B2b + B2c (D-38, D-39) |
| Shadow `search_display` (identity blob) | — | ✓ B2f (D-59) |

## Code map (modernized)

| Concern | Location |
|---------|----------|
| Search SQL | `web/api/raa_api/search.py` |
| Display formatting | `web/api/raa_api/display.py` |
| API routes | `web/api/raa_api/main.py` |
| Personen UI | `web/frontend/static/index.html`, `personen.js` |
| Aanstellingen UI | `web/frontend/static/aanstellingen.html`, `aanstellingen.js` |
| Shared JS | `web/frontend/static/common.js`, `entity-detail.js` |
| Import / purge | `scripts/import_release.py` |
| Life dates (EDTF + shadow) | `raa_life_dates/`, `scripts/shadow_life.py` |
| Search display (identity blob) | `raa_search_display/`, `scripts/backfill_search_display.py` |
| Entity spans | `raa_entity_spans/` (B2e), `import_release.py` |
| EDTF search SQL | `web/api/raa_api/edtf_bounds.py` |
