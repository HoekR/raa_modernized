# Historian validation matrix — Milestone B3

Working document for **Milestone B validation** ([PLAN.md](../PLAN.md)): compare the modern pilot against the [legacy Huygens app](https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/) using realistic research questions (RQ).

> **IDs differ.** Legacy Huygens `/app/personen/{id}` numbers are **not** pilot `persoon.id` values. Do not use legacy IDs in `?person=` deep links. Example: legacy [6448](https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/app/personen/6448) (Tjaerd baron van Aylva) → pilot **`21009`** — see [MIGRATION_LOG.md](MIGRATION_LOG.md) D-58.

**How to use**

1. Run each RQ in **legacy** (note total hits + spot-check 2–3 rows).
2. Run the same RQ in the **pilot** (`http://127.0.0.1:8000/static/…` or deployed URL).
3. Fill in **Legacy** / **Δ** / **Verdict** / **Notes**.
4. Log meaningful gaps in [MIGRATION_LOG.md](MIGRATION_LOG.md) and open B3 fix slices in PLAN.md.

**Pass criteria (default)**

| Check | Pass |
|-------|------|
| **Count** | Within ±2% of legacy, or explainable (divperioden purge, shadow dates, period scope) |
| **Spot-check** | Same 3 persons/offices appear in first page (order may differ if sort differs) |
| **Detail** | Person detail shows bovenlokaal/namens, bronnen, life dates where legacy does (compare same **person**, not same numeric id) |
| **Blocked** | Pilot cannot answer RQ at all → **fail** + note missing filter/UI |

**Pilot baseline** counts below were captured 2026-07-13 against Postgres `release dev` after B2e import. Re-run API smoke if data changes.

```bash
# from repo root — requires Postgres with imported data
uv run python scripts/validation_rq_smoke.py
```

---

## Personen (`/static/index.html`)

| ID | Research question | Period | Pilot steps | Pilot baseline | Legacy | Δ | Verdict | Notes |
|----|-------------------|--------|-------------|----------------|--------|---|---------|-------|
| **P1** | Wie waren de **Aylva's** in de Republiek? | Republiek, scoped | `q` = `aylva` | **37** | | | | Wildcard variant: `van*aylva` → 31 |
| **P2** | Wie werd **geboren tussen 1700 en 1750**? | Republiek | `geboorte` = `1700/1750`; default incl. shadow | **1616** | | | | Retry with **zoek exacte datums**; expect lower |
| **P3** | Wie bekleedde **gedeputeerde** bij de **Gedeputeerde Staten van Friesland**? | Republiek | functie chip *gedeputeerde* (id 561); instelling *Gedeputeerde Staten van Friesland* (id 171); **en** | **411** personen | | | | Legacy: functie + instelling multi-select |
| **P4** | Wie bekleedde **burgemeester** in **Utrecht** (provinciaal)? | Republiek | functie *burgemeester*; provincie *Utrecht*; optional stand | | | | | geo + stand/adel UI (B3c) |
| **P5** | Wie had een aanstelling **1750–1770**? | Republiek | `van`=`1750`, `tot`=`1770` | **2841** | | | | B3d aanstellingsdatum overlap on personen |

**API reference (P3)**

```json
POST /api/search/personen
{
  "period": "republiek",
  "period_mode": "scoped",
  "filters": { "functie_id": ["561"], "instelling_id": ["171"] },
  "functie_match": "any",
  "instelling_match": "all",
  "size": 1
}
```

---

## Aanstellingen (`/static/aanstellingen.html`)

| ID | Research question | Period | Pilot steps | Pilot baseline | Legacy | Δ | Verdict | Notes |
|----|-------------------|--------|-------------|----------------|--------|---|---------|-------|
| **A1** | **Gedeputeerden** in de **Gedeputeerde Staten van Friesland** — wie, wanneer? | Republiek | functie + instelling as P3; nested instelling→functie | **677** aanstellingen | | | | Compare nested grouping to legacy |
| **A2** | **Burgemeesters** met vertegenwoordiging **Utrecht** | Republiek | functie burgemeester + provincie Utrecht | | | | | |
| **A3** | Zelfde functie **over alle perioden** (cross-period) | **Alle perioden** | functie *schout* or *raadspensionaris*; overall mode | | | | | Expect larger vocab; clutter OK |
| **A4** | Aanstellingen in een **zittingstermijn** (bijv. 1750–1770) | Republiek | `van`=`1750`, `tot`=`1770` (jaar of YYYY-MM-DD) | | | | | B3d: year-capable van/tot on aanstellingen + personen |

---

## Instellingen (`/static/instellingen.html`)

| ID | Research question | Period | Pilot steps | Pilot baseline | Legacy | Δ | Verdict | Notes |
|----|-------------------|--------|-------------|----------------|--------|---|---------|-------|
| **I1** | Waar vind ik **Staten van Friesland**? | Republiek | `q` = `staten*friesland` | **1** hit (id 459) | | | | Open detail → functies + toelichting |
| **I2** | Welke **raden** bestaan in de Republiek? | Republiek | `q` = `*raad*` **or** A–Z letter **R** | | | | | B3e browse A–Z |
| **I3** | Wat doet de instelling **Provinciale Rekenkamer van Friesland**? | Republiek | search → detail; read toelichting + functie spans | id **337** | | | | |
| **I4** | Instellingen **Bataafs-Franse tijd** vs Republiek | Compare | Run same `q` in batfra vs republiek period | | | | | Period selector behaviour |

---

## Functies (`/static/functies.html`)

| ID | Research question | Period | Pilot steps | Pilot baseline | Legacy | Δ | Verdict | Notes |
|----|-------------------|--------|-------------|----------------|--------|---|---------|-------|
| **F1** | Welke **gedeputeerde**-varianten zijn er? | Republiek | `q` = `gedeputeerde` | **3** (extraordinaris / ordinarius / gedeputeerde) | | | | |
| **F2** | Waar komt **raadspensionaris** voor? | Republiek | open functie detail → institutionele contexten + spans | | | | | B2e: first/last + context list |
| **F3** | Wie bekleedde functie X? (navigatie) | Republiek | functie detail → link **Personen die deze functie bekleedden** | | | | | Deep link `?functie_id=` on personen |
| **F4** | Functie in **meerdere instellingen** tegelijk | Republiek | pick functie with high `instelling_count` on profile | | | | | Validates D-55–D-57 caveat copy |

---

## Cross-cutting checks (after per-context pass)

| ID | Check | Pass? | Notes |
|----|-------|-------|-------|
| **X1** | Period **Republiek** includes `republiek_friezen` rows | | |
| **X2** | Wildcards `*` `?` match legacy on naam fields | | |
| **X3** | Person detail parity — Tjaerd baron van Aylva | | Legacy id **6448** only on Huygens; pilot `?person=**21009**` ([open](http://127.0.0.1:8000/static/index.html?person=21009)) |
| **X4** | Functie/instelling **en/of** matches legacy for P3-style RQ | | |
| **X5** | EDTF **P2** with/without shadow — sensible difference | | |

---

## Outcomes → action

| Verdict | Action |
|---------|--------|
| **Pass** | Mark row in MIGRATION_LOG parity matrix |
| **Pass with note** | Document difference (e.g. shadow dates, modern-only feature) |
| **Fail — filter gap** | Add to B3 slice (UI chip, date range, sort, pagination) |
| **Fail — SQL bug** | Fix `search.py` + regression test |
| **Fail — data** | Check import / `raa_convert` / divperioden purge |

When ≥12/16 core RQs pass and all **X** checks pass, close Milestone B validation in PLAN.md.
