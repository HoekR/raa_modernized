# Career pattern analysis (research lab)

Standalone analysis package for appointment **sequences** and **transitions**.
Not part of the public search UI or editorial app.

**Framing:** politics and influence (elite continuity, office layers, wetsverzetting). Research questions: [CAREER_RQS.md](CAREER_RQS.md).

## Package

| Module | Role |
|--------|------|
| `raa_career_patterns.events` | Load/normalize `raa.aanstelling` (+ name joins) |
| `raa_career_patterns.sequences` | Per-person ordered sequences + overlap groups |
| `raa_career_patterns.transitions` | Consecutive pairs + aggregate matrices |
| `raa_career_patterns.filters` | Period flags, year window, min posts |
| `raa_career_patterns.discontinuity` | F-RQ0: cut vs quiet windows, influence layers |

## Date and overlap policy

- Calendar dates use `pd.Period(..., freq="D")` (same caveat as entity spans: no `pd.to_datetime` for pre-1678).
- Plausible years: 1400–1900; garbage years nulled via `sanitize_aanstelling_years`.
- **Dated** posts (`van` usable) get `seq_idx` 0..n−1 per person, sorted by `van` then `aanstelling_id`.
- **Complete office only (default):** drop appointments missing `functie_id` or `instelling_id` before sequences/transitions. Those gaps are mostly content-related; retaining them creates a fake “unknown” node in matrices. CLI: `--keep-incomplete-office` to retain.
- **Reappointments:** consecutive rows with the same office (`functie_id` × `instelling_id`) collapse into **one job spell** (`n_appointments` ≥ 1; span from first `van` to latest `tot`). Returning to the same office after a different job is a **second** spell. Pairwise transitions therefore skip A→A reappointments.
- **Undated** posts keep `seq_idx` / `overlap_group_id` null and do not enter transitions.
- Overlapping intervals (missing `tot` = open-ended) share an `overlap_group_id` within a person. Endpoint-touching spans (`tot` of A equals `van` of B) are **not** overlaps.
- Consecutive overlapping steps are emitted with `skipped_overlap=true` and **excluded** from aggregate matrices.
- Do **not** invent continuity between institutions or fill gaps into one ambtsketen.

## Aggregation grains

- `functie` — functie_id → functie_id
- `instelling` — instelling_id → instelling_id
- `office` — `(functie_id, instelling_id)` encoded as `"f:i"` strings in the matrix

Matrix columns: `from_id`, `to_id`, `count`, `from_label`, `to_label`, `probability` (row-normalized), `grain`.

## CLI

Requires Postgres with imported `raa.*` data (`DATABASE_URL` or default local URL).

```bash
uv run python scripts/career_patterns.py export-events
uv run python scripts/career_patterns.py sequences --drop-undated
uv run python scripts/career_patterns.py transitions --drop-undated
uv run python scripts/career_patterns.py discontinuity
uv run python scripts/career_patterns.py overview --with-discontinuity
```

Start exploration with **`overview`** (corpus size, career-length, eras, top offices, F-RQ0 cut vs quiet).

Outputs (scratch, via `data_io`):

- `career_events`
- `career_sequences`
- `career_transitions`
- `career_transition_matrix`
- `career_discontinuity_summary` / `career_discontinuity_crossings` (F-RQ0)

## Notebook

[`notebooks/career_patterns_explore.ipynb`](../notebooks/career_patterns_explore.ipynb) is the main exploration UI: corpus charts, F-RQ0 continuity (incl. 1618/1651/**1672**/1713/1795/1813), dense-subgraph circulation **by era**, coverage-density caveat, sample careers.

## Backlog (not v1)

Pathways into high-influence offices, concurrent stacking, mobility / path mining / bipartite (Track F5–F7; UI 14c remains separate).
