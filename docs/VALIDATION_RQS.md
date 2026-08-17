# Historian validation matrix — Milestone B3 / B4b

Working document for **Milestone B validation** ([PLAN.md](../PLAN.md)): compare the modern pilot against the [legacy Huygens app](https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/) using realistic research questions (RQ).

> **IDs differ (D-58, corrected 2026-08-16).** Huygens `/app/personen/{id}` is a **different namespace** from `extab.pkl` / pilot `persoon.id`.
>
> - Huygens [6448](https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/app/personen/6448) = **Tjaerd baron van Aylva** (1712–1757, Waardenburg en Neerijnen).
> - Pilot biographical match = **`21510`** (not 21009). Deep link: `http://127.0.0.1:8000/static/index.html?person=21510`
> - Pilot **21009** = earlier Tjaerd van Aylva (1644–1705).
> - Extab id **6448** is unrelated (Peter Joseph Berger) — do not use Huygens URL numbers as pilot ids.

**How to use**

1. Run each RQ in **legacy** (note total hits + spot-check 2–3 rows).
2. Run the same RQ in the **pilot** (`http://127.0.0.1:8000/static/…`).
3. Fill in **Legacy** / **Δ** / **Verdict** / **Notes**.
4. Log meaningful gaps in [MIGRATION_LOG.md](MIGRATION_LOG.md).

**Pass criteria (default)**

| Check | Pass |
|-------|------|
| **Count** | Within ±2% of legacy, or explainable (divperioden purge, shadow dates, period scope) |
| **Spot-check** | Same 3 persons/offices appear in first page (order may differ if sort differs) |
| **Detail** | Person detail shows bovenlokaal/namens, bronnen, life dates where legacy does (compare same **person**, not same numeric id) |
| **Blocked** | Pilot cannot answer RQ at all → **fail** + note missing filter/UI |

**B4b status (2026-08-16):** pilot baselines + automated X1–X5 locked; structural/detail RQs verified against Huygens pages where possible. **Legacy hit counts** still need interactive Huygens form fills (no public GET search API).

```bash
# from repo root — requires Postgres with imported data
uv run python scripts/validation_rq_smoke.py --assert
# or: make check-db
```

---

## Personen (`/static/index.html`)

| ID | Research question | Period | Pilot steps | Pilot baseline | Legacy | Δ | Verdict | Notes |
|----|-------------------|--------|-------------|----------------|--------|---|---------|-------|
| **P1** | Wie waren de **Aylva's** in de Republiek? | Republiek, scoped | `q` = `aylva` | **37** | *TBD form* | | **pilot OK** | Wildcard `van*aylva` → 31; fill Legacy count interactively |
| **P2** | Wie werd **geboren tussen 1700 en 1750**? | Republiek | `geboorte` = `1700/1750`; default incl. shadow | **1616** | *TBD form* | | **pilot OK / modern-only** | Shadow expands count vs exact (see X5); Legacy has no EDTF |
| **P3** | Wie bekleedde **gedeputeerde** bij de **Gedeputeerde Staten van Friesland**? | Republiek | functie *gedeputeerde* (561); instelling *Gedeputeerde Staten van Friesland* (171); **en** | **411** personen | *TBD form* | | **pilot OK** | En/of wiring verified (X4) |
| **P4** | Wie bekleedde **burgemeester** in **Utrecht** (provinciaal)? | Republiek | functie *burgemeester*; provincie *Utrecht* | *run UI* | *TBD form* | | **pilot capable** | B3c geo + stand/adel |
| **P5** | Wie had een aanstelling **1750–1770**? | Republiek | `van`=`1750`, `tot`=`1770` | **2841** | *TBD form* | | **pilot OK** | B3d; modern overlap semantics |

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
| **A1** | **Gedeputeerden** in de **Gedeputeerde Staten van Friesland** — wie, wanneer? | Republiek | functie + instelling as P3; nested | **677** aanstellingen | *TBD form* | | **pilot OK** | Nested grouping shipped |
| **A2** | **Burgemeesters** met vertegenwoordiging **Utrecht** | Republiek | functie + provincie Utrecht | *run UI* | *TBD form* | | **pilot capable** | |
| **A3** | Zelfde functie **over alle perioden** | **Alle perioden** | functie *schout* (id 1316); overall | *run UI* | *TBD form* | | **pilot capable** | Cross-period clutter expected |
| **A4** | Aanstellingen **1750–1770** | Republiek | `van`=`1750`, `tot`=`1770` | *run UI* | *TBD form* | | **pilot OK** | Year-capable van/tot |

---

## Instellingen (`/static/instellingen.html`)

| ID | Research question | Period | Pilot steps | Pilot baseline | Legacy | Δ | Verdict | Notes |
|----|-------------------|--------|-------------|----------------|--------|---|---------|-------|
| **I1** | Waar vind ik **Staten van Friesland**? | Republiek | `q` = `staten*friesland` | **1** (id 459) | form exists | | **pass with note** | Legacy has same wildcard form; count TBD interactively |
| **I2** | Welke **raden** bestaan in de Republiek? | Republiek | `q` = `*raad*` or A–Z **R** | **~25** (extab) | form exists | | **pilot OK** | B3e A–Z browse |
| **I3** | **Provinciale Rekenkamer van Friesland** toelichting | Republiek | detail id **337** | profile | page exists | | **pass with note** | Compare toelichting + spans vs legacy detail |
| **I4** | Instellingen batfra vs republiek | Compare | same `q`, switch period | *run UI* | n/a | | **pilot OK** | Modern period selector (D-20) |

---

## Functies (`/static/functies.html`)

| ID | Research question | Period | Pilot steps | Pilot baseline | Legacy | Δ | Verdict | Notes |
|----|-------------------|--------|-------------|----------------|--------|---|---------|-------|
| **F1** | **gedeputeerde**-varianten | Republiek | `q` = `gedeputeerde` | **3** | *TBD form* | | **pilot OK** | |
| **F2** | Waar komt **raadspensionaris** voor? | Republiek | functie id **1038** detail → spans | profile | | | **pass with note** | B2e corpus witnesses; modern-only |
| **F3** | Wie bekleedde functie X? | Republiek | detail → personen deep link | works | | | **pass** | `?functie_id=` on personen |
| **F4** | Functie in **meerdere instellingen** | Republiek | high `instelling_count` profile | works | | | **pass with note** | D-55–D-57 caveat copy |

---

## Cross-cutting checks

```bash
uv run python scripts/validation_rq_smoke.py --assert
```

| ID | Check | Pass? | Notes |
|----|-------|-------|-------|
| **X1** | Republiek includes `republiek_friezen` | **PASS** (automated) | |
| **X2** | Wildcards on `search_display` | **PASS** (automated) | |
| **X3** | Person detail — Tjaerd baron van Aylva | **PASS with note** | Huygens [6448](https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/app/personen/6448) ↔ pilot **21510** (1712–1757). Earlier namesake = **21009**. Detail fields (heerlijkheid, opmerkingen, bovenlokaal) present in pilot. |
| **X4** | Functie/instelling en/of | **PASS** (automated pilot) | Legacy count compare still TBD |
| **X5** | EDTF P2 shadow vs exact | **PASS** (automated) | Modern-only feature |

---

## B4b outcome (2026-08-16)

| Gate | Status |
|------|--------|
| Pilot can answer all 16 RQs (no blocked filters) | **Yes** (B3a–e) |
| Automated X1–X5 | **Pass** (`--assert`) |
| ID concordance sample corrected | **Yes** (6448 biography → 21510) |
| Interactive Legacy **hit counts** filled | **Open** — needs ~1–2 h on Huygens search forms |
| Close B3 (≥12/16 Legacy-compared) | **Deferred** until Legacy count cells filled |

**Next:** Milestone **C** (SvelteKit) may proceed; finish Legacy count cells when convenient for B3 formal close / B4b complete.

---

## Outcomes → action

| Verdict | Action |
|---------|--------|
| **Pass** | Mark row in MIGRATION_LOG parity matrix |
| **Pass with note** | Document difference (e.g. shadow dates, modern-only feature) |
| **Fail — filter gap** | Add to B3 slice |
| **Fail — SQL bug** | Fix `search.py` + regression test |
| **Fail — data** | Check import / `raa_convert` / divperioden purge |
