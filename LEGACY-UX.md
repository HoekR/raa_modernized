# Legacy UX — Huygens RAA search model

Reference for parity work against the live Huygens UI and the original Zope/SQLObject app in `RepertoriumAmbtenarenAmbtsdragers`.

- Zoekhulp (overview): https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/zoekhulp
- Field help (in-app `?` tooltips): https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/app/help
- Legacy source: `src/raa/browser/templates/`, `query.py`, `form.py`

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

**Not yet in pilot:** this split, namens line, en/of functie/instelling, full personen field set.

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

## Parity checklist

| Feature | Legacy | Pilot |
|---------|--------|-------|
| Personen naam / alias / titels / dates | ✓ | partial (single `q`) |
| Vertegenwoordiging search | ✓ | ✓ (2026-07-12 — see [MIGRATION_LOG](docs/MIGRATION_LOG.md)) |
| Aanstellingen nested grouping | ✓ | API only; flat UI |
| Person detail bovenlokaal / namens | ✓ | — |
| Functie/instelling en/of | ✓ | — |
| Instelling → functies → aanstellingen | ✓ | partial |
| `republiek_friezen` period option | — | Separate **edit track** in convert; merged into Republiek in search |

## Code map (modernized)

| Concern | Location |
|---------|----------|
| Search SQL | `web/api/raa_api/search.py` |
| API routes | `web/api/raa_api/main.py` |
| Personen UI | `web/frontend/static/index.html`, `personen.js` |
| Aanstellingen UI | `web/frontend/static/aanstellingen.html`, `aanstellingen.js` |
| Shared JS | `web/frontend/static/common.js` |
| Import / purge | `scripts/import_release.py` |
