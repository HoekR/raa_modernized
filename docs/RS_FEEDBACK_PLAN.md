# RS feedback refinement plan

> **Source:** `CommentaarApplicatieRik_RS.txt` (2026-08)  
> **Status:** implementation in progress (2026-09-18)  
> **Related:** [UI_REFINEMENT_PLAN.md](UI_REFINEMENT_PLAN.md), [SURF_DEMO.md](SURF_DEMO.md), [START.md](START.md), [LIFE_DATES.md](LIFE_DATES.md)

Historian feedback on the SURF/public pilot. Product calls closed: **C2 lock**, **B3 listing+titles**, **D2 hybrid history**.

## Item register


| ID  | Remark (short)                                             | Effort | Status |
| --- | ---------------------------------------------------------- | ------ | ------ |
| A1–A5, B2, B4, B6 | Copy / sort / histogram (earlier)                    | S      | **done** |
| A6  | Uncertainty: `ca.` not bare `~`                            | S–M    | **done** |
| B1  | Personen-bij-instelling chronological (`sort=van`)         | S–M    | **done** |
| B3  | Listing `achternaam, voornaam` + titles (+ cache)          | S–M    | **done** |
| B5  | Adel visible in result rows                                | S–M    | **done** |
| C1  | Hide stand options with count 0 in period                  | M      | **done** |
| C2  | Lock instelling when refining from detail                  | M      | **done** |
| C3–C5 | Provincie filters + stacked namens (`›`) + Ackema path   | M      | **done** (display/filter; verify Ackema on live DB) |
| D1  | Inleiding link home + nav                                  | S–M    | **done** |
| D2  | Hybrid push/replace history (personen + aanstellingen)     | M      | **done** |
| D3  | Toelichting footnote stays on page                         | S–M    | **done** |
| E1  | Sanitize garbage appointment years (e.g. 2031)             | M      | **done** (import + spans) |
| E2  | Merge duplicate Staten-Generaal                            | S–M    | **script** `scripts/merge_staten_generaal.py` (dry-run / `--apply`) |


## Product calls (confirmed)

| ID | Decision |
|----|----------|
| C2 | Lock + Ontgrendel |
| B3 | Surname-first + titles, ~72 chars, `listing_naam` cache |
| D2 | Hybrid history (C) for personen + aanstellingen |

## Follow-ups on a loaded DB

```bash
# listing_naam + search_display cache
uv run python scripts/backfill_search_display.py

# Staten-Generaal merge (inspect first)
uv run python scripts/merge_staten_generaal.py
uv run python scripts/merge_staten_generaal.py --apply

# Re-import to rebuild spans with year sanitize
./scripts/dev.sh --import-only   # stop API first if running
```

## Changelog

| Date | Change |
|------|--------|
| 2026-08-20 | Initial plan; E2 revised S–M |
| 2026-08-20 | Shipped A1–A5, B4 |
| 2026-08-21 | Product calls confirmed (C2, B3, D2) |
| 2026-09-18 | Implemented remaining M1–M4 items in order |
