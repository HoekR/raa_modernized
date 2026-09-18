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
| `docs/START.md` | **How to start the local app** (API + UIs) |
| `docs/DATA.md` | Tiers, phases, manifest workflow |
| `data_manifest.toml` | Tier roots and registered datasets |
| `notebooks/` | Jupyter workspace (explore phase) |
| `output/` | Local scratch-tier fallback (gitignored; see `output/README.md`) |
| `data_io/` | Manifest I/O and provenance helpers |
| `web/` | FastAPI search API + static frontend + SvelteKit UI (`web/ui/`) |
| `scripts/import_release.py` | Load `extab.pkl` into Postgres |
| `scripts/validation_rq_smoke.py` | Pilot baseline counts + X1–X5 for [VALIDATION_RQS.md](docs/VALIDATION_RQS.md) (`--assert`) |
| `scripts/dev.sh` | **Local API:** Postgres + import-if-empty + API (D-53) |
| `scripts/start_app.sh` / `stop_app.sh` / `restart_app.sh` | Full local stack (API + UIs) — see [docs/START.md](docs/START.md) |
| `Makefile` | `make check` / `make check-db` / `make smoke` |

## Web app (local)

Full start guide: **[docs/START.md](docs/START.md)**.

```bash
./scripts/start_app.sh     # Postgres + API :8000 + UI :5173 + redactie :5174
./scripts/stop_app.sh      # stop API + UIs (Postgres stays up)
./scripts/restart_app.sh   # bounce API + UIs
```

One-time: copy `config.local.toml.example` / `data_manifest.local.toml.example`, then `uv sync` and `npm install` in `web/ui` and `web/admin`.

**Checks**

```bash
make check       # unit tests (no DB)
make check-db    # + RQ baselines and X1–X5 (Postgres must be up + imported)
```

<details>
<summary>Manual steps (legacy / debugging)</summary>

```bash
# Postgres via compose (or: docker start raa_pg if you still use the old named container)
docker compose -f web/docker-compose.yml up -d db

cd ~/develop/raa_modernized
uv run python scripts/import_release.py --skip-validate   # from repo root, not web/api

cd web/api && uv sync
uv run uvicorn raa_api.main:app --reload --host 127.0.0.1 --port 8000
```

If `docker run --name raa_pg` conflicts, use `docker start raa_pg` or migrate to compose only.

</details>

Search store: **PostgreSQL** (Elasticsearch deferred). See `PLAN.md` and `docs/MIGRATION_LOG.md` for decisions.

**When the stack stabilizes (D-54):** the compose API service will use **Gunicorn + Uvicorn workers** instead of `uvicorn --reload`; `dev.sh` keeps reload for day-to-day work.

## Cursor / agents

Read **`AGENTS.md`** first. Rules also load from `.cursor/rules/project-standards.mdc` and `.cursorrules`.

## SURF shared demo

Team pilot on SURF Research Cloud: [docs/SURF_DEMO.md](docs/SURF_DEMO.md) — `./scripts/surf_stack.sh up` (nginx on :80).
