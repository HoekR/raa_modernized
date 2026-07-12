# raa-modernized

DH data pipeline with manifest-based paths (`data_manifest.toml` + `data_io`).

## Setup

```bash
# Bootstrap already ran `uv sync` and installed the Jupyter kernel.
# Re-run `uv sync` if you later change dependencies.
# edit data_manifest.toml — tier roots and [datasets.*]
# optional when scratch drive is unplugged:
cp data_manifest.local.toml.example data_manifest.local.toml
# Data registry view (manifest-declared datasets + on-disk status)
uv run python -m data_io.check
```

Open the workspace profile in Cursor or VS Code:

```bash
cursor raa-modernized.code-workspace
```

## Layout

| Path | Role |
|------|------|
| `AGENTS.md` | Agent instructions — read before pipeline work |
| `PLAN.md` | Target architecture, phases, open work |
| `docs/MIGRATION_LOG.md` | **Decision register + implementation log** (how/why we migrated) |
| `LEGACY-UX.md` | Legacy Huygens search UX reference (zoekhulp mapping) |
| `docs/DATA.md` | Tiers, phases, manifest workflow |
| `data_manifest.toml` | Tier roots and registered datasets |
| `notebooks/` | Jupyter workspace (explore phase) |
| `output/` | Local scratch-tier fallback (gitignored; see `output/README.md`) |
| `data_io/` | Manifest I/O and provenance helpers |
| `web/` | FastAPI search API + static frontend |
| `scripts/import_release.py` | Load `extab.pkl` into Postgres |

## Web app (local)

```bash
# Postgres (first time)
docker run -d --name raa_pg \
  -e POSTGRES_USER=raa -e POSTGRES_PASSWORD=raa -e POSTGRES_DB=raa_modernized \
  -p 5432:5432 postgres:16

cd ~/develop/raa_modernized
cp config.local.toml.example config.local.toml   # once
cp data_manifest.local.toml.example data_manifest.local.toml  # edit tier root
uv run python scripts/import_release.py --skip-validate

cd web/api
uv sync
uv run uvicorn raa_api.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 — search contexts: personen, aanstellingen, instellingen, functies.

Search store: **PostgreSQL** (Elasticsearch deferred). See `PLAN.md` and `docs/MIGRATION_LOG.md` for decisions.

## Cursor / agents

Read **`AGENTS.md`** first. Rules also load from `.cursor/rules/project-standards.mdc` and `.cursorrules`.
