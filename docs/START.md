# Start the app (local)

Day-to-day local stack: Postgres + API + SvelteKit UIs.

SURF / shared demo host: [SURF_DEMO.md](SURF_DEMO.md).  
Editorial walkthrough: [EDITORIAL_DEMO.md](EDITORIAL_DEMO.md).

## Prerequisites

- Docker (Postgres container)
- [uv](https://docs.astral.sh/uv/)
- Node / npm (for the UIs)

## One-time setup

From the repo root:

```bash
cp config.local.toml.example config.local.toml
cp data_manifest.local.toml.example data_manifest.local.toml
# Edit data_manifest.local.toml so raa_extab resolves to your extab.pkl

uv sync
cd web/ui && npm install && cd ../..
cd web/admin && npm install && cd ../..
```

For redactie, set in `config.local.toml`:

```toml
[editorial]
enabled = true
api_key = "…"          # paste this at /login
editor_id = "you"
cors_origins = ["http://localhost:5174", "http://127.0.0.1:5174"]
```

## Start / stop / restart (one command)

Preferred: background scripts (API + public UI + redactie). Logs and PIDs live in `.run/`.

```bash
./scripts/start_app.sh              # Postgres + API :8000 + UI :5173 + redactie :5174
./scripts/stop_app.sh               # stop API + UIs (Postgres stays up)
./scripts/restart_app.sh            # stop then start
```

| Command | Effect |
|---------|--------|
| `./scripts/start_app.sh` | Full stack in background |
| `./scripts/start_app.sh --no-admin` | Skip redactie |
| `./scripts/start_app.sh --import` | Re-import extab, then start |
| `./scripts/stop_app.sh` | Stop API + UIs |
| `./scripts/stop_app.sh --db` | Also stop Postgres (`dev.sh stop`) |
| `./scripts/restart_app.sh` | Bounce API + UIs |
| `./scripts/restart_app.sh --db` | Bounce Postgres too |
| `./scripts/restart_app.sh --import` | Re-import on restart |
| `./scripts/app.sh status` | PIDs + listening ports |

URLs after `start_app.sh`:

| Service | URL |
|---------|-----|
| API | http://127.0.0.1:8000 |
| Public UI | http://127.0.0.1:5173 |
| Redactie | http://127.0.0.1:5174 |

Login (redactie): paste `[editorial].api_key` from `config.local.toml`.

Tail logs:

```bash
tail -f .run/api.log .run/ui.log .run/admin.log
```

## Manual (foreground, three terminals)

Use this when you want reload output in the terminal.

**Terminal 1 — database + API**

```bash
./scripts/dev.sh
```

→ http://127.0.0.1:8000

**Terminal 2 — public UI**

```bash
cd web/ui && npm run dev
```

→ http://127.0.0.1:5173

**Terminal 3 — redactie (optional)**

```bash
cd web/admin && npm run dev
```

→ http://127.0.0.1:5174

**Stop:** Ctrl+C in each terminal. To also tear down compose Postgres: `./scripts/dev.sh stop`.

## `dev.sh` variants

| Command | Effect |
|---------|--------|
| `./scripts/dev.sh --db-only` | Postgres only |
| `./scripts/dev.sh --prod` | Gunicorn + Uvicorn workers (no reload) |
| `./scripts/dev.sh --import` | Re-import extab, then start API — **stop** a running API first |
| `./scripts/dev.sh --import-only` | Re-import only; does not start API |
| `./scripts/dev.sh stop` | Compose down (volume kept) |

## Checks

```bash
make check       # unit tests (no DB)
make check-db    # + RQ baselines (Postgres must be up)
```
