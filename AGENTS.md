# Agent instructions — RAA Modernized

Modern web port of the **Huygens RAA** (Repertorium Aanstellingen Amsterdam) corpus: `extab.pkl` → Postgres → FastAPI search → SvelteKit UI, plus a separate **redactie** app for editorial amendments.

Read **`PLAN.md`**, **`docs/MIGRATION_LOG.md`**, and **`docs/DATA.md`** before pipeline or web work. Legacy UX reference: **`LEGACY-UX.md`**.

## What lives where

| Path | Role |
|------|------|
| `data_manifest.toml` | Dataset registry; canonical input `raa_extab` |
| `scripts/import_release.py` | Prepare extab → load `raa_staging` → merge into `raa.*` |
| `scripts/merge_release.py` | Standalone staging merge (editorial conflicts) |
| `scripts/dev.sh` | Local stack: Postgres + import-if-empty + API `:8000` |
| `raa_life_dates/` | EDTF, shadow life years, plausibility validation |
| `raa_search_display/` | `search_display`, listing names |
| `raa_entity_spans/` | Institution/function span tables |
| `web/api/` | FastAPI (`raa_api`) — search, detail, editorial API |
| `web/ui/` | Public SvelteKit UI `:5173` |
| `web/admin/` | Editorial SvelteKit app `:5174` |
| `web/shared/` | Shared fetch helpers (`@raa/shared`) |
| `config.local.toml` | DB URL, `[editorial]` (gitignored; copy from `.example`) |

## Milestone status (see `PLAN.md` for detail)

| Track | State |
|-------|--------|
| **B** | Postgres search pilot — shipped (B2–B4 largely done) |
| **C** | SvelteKit UI — in progress (C1–C3 shipped; static pilot kept until beta) |
| **D** | Deploy read-only pilot — planned |
| **E** | Editorial layer — **E0–E5 shipped** (amendments, grid, Excel import) |

## Data paths (strict)

- **Never** hardcode absolute paths in Python (`/Users/...`, `/Volumes/...`).
- Register datasets in `data_manifest.toml`, then:

```python
from data_io import resolve, load, save_semi_structured, save_parquet
```

- After manifest changes: `uv run python -m data_io.check`
- Pipeline outputs → scratch tier via `save_*` (provenance sidecars automatic).
- Do not drop archival metadata fields when transforming extab-derived records.

Primary corpus input: **`raa_extab`** (logical name for `extab.pkl`).

## Import and database

```bash
./scripts/dev.sh              # Postgres + import if empty + API
./scripts/dev.sh --import     # re-import (stop running dev.sh first)
uv run python scripts/import_release.py
```

- Import loads **`raa_staging`**, then merges into **`raa.*`**; **`editorial.*`** is preserved.
- Re-import may create rows in **`editorial.conflicts`** when base data drifts from active amendments.
- Life-date pipeline, shadow enrichment, garbage-year sanitization: [docs/LIFE_DATES.md](docs/LIFE_DATES.md).

## Web layer

| App | URL | Purpose |
|-----|-----|---------|
| API | http://localhost:8000 | Search, detail, editorial endpoints |
| Public UI | http://localhost:5173 | `cd web/ui && npm run dev` |
| Redactie | http://localhost:5174 | `cd web/admin && npm run dev` |

**Config** (repo root `config.local.toml`):

```toml
[database]
url = "postgresql+psycopg://..."

[editorial]
enabled = true
api_key = "..."
editor_id = "..."
cors_origins = ["http://localhost:5174", "http://127.0.0.1:5174"]
```

**Editorial:** [docs/EDITORIAL.md](docs/EDITORIAL.md) · demo [docs/EDITORIAL_DEMO.md](docs/EDITORIAL_DEMO.md) · SURF host [docs/SURF_DEMO.md](docs/SURF_DEMO.md)

- Amendments in `editorial.amendments`; effective = amendment ?? base.
- Admin routes: instelling toelichting, persoon/aanstelling fields, werklijst grid, conflicts.
- Persoon date edits use exact **j / m / d** parts; save triggers `refresh_persoon_derived`.

## Session workflow

1. Read `PLAN.md` — current milestone and open todos.
2. Log decisions in `docs/MIGRATION_LOG.md` when architecture or behaviour changes.
3. `uv run python -m data_io.check` before new pipeline work.
4. Web smoke: `./scripts/dev.sh` + public UI + (if editorial) admin login.

## Tests

```bash
make check          # unit tests, no DB
make check-db       # + validation RQ baselines (Postgres up)
cd web/api && uv run pytest tests/ -q
```

Editorial subset: `uv run pytest tests/test_editorial*.py -q`

## Common mistakes

| Wrong | Right |
|-------|--------|
| `pd.read_parquet("/Volumes/.../extab...")` | `load("raa_extab")` or manifest `resolve("raa_extab")` |
| Edit `extab.pkl` or Postgres `raa.*` by hand for corrections | Editorial amendments via `web/admin` or API |
| Re-import while `dev.sh` is running | Stop dev.sh (Ctrl+C), then `--import` |
| `pd.to_datetime` for pre-1678 calendar dates | `pd.Period(..., freq="D")` — see project rules |
| Hardcode editorial API key in source | `[editorial].api_key` in `config.local.toml` |

## Cursor rules

Also loaded: `.cursorrules`, `.cursor/rules/project-standards.mdc`.

Bootstrapped from `dighum_web_template`; RAA-specific decisions live in this repo's `PLAN.md` and `MIGRATION_LOG.md`, not the template wisdom index.
