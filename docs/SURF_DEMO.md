# SURF demo / pilot host

Run the RAA stack on a **SURF Research Cloud** VM. One entry point: [`scripts/surf_stack.sh`](../scripts/surf_stack.sh).

See also: [EDITORIAL_DEMO.md](EDITORIAL_DEMO.md) (what to show), [EDITORIAL.md](EDITORIAL.md) (API reference).

## Quick start (recommended — single URL on port 80)

```bash
git clone <repo> ~/raa_modernized && cd ~/raa_modernized

# 1. Config (edit hostname + api_key)
./scripts/surf_stack.sh setup
nano config.local.toml          # YOUR-SURF-HOST, api_key
nano data_manifest.local.toml   # path to extab on /data volume

# 2. Mount corpus on VM (e.g. SURF volume at /data/raa_convert/extab.pkl)
export DATA_ENV=researchcloud

# 3. Database + import (once) — OR skip with restore_demo_db.sh (Path C)
./scripts/surf_stack.sh import

# 4. Build static UI + start db + api + nginx
./scripts/surf_stack.sh build-ui
export SURF_PUBLIC_HOST=your-vm.surf.nl
./scripts/surf_stack.sh up
```

Share with team:

| URL | App |
|-----|-----|
| `http://YOUR-SURF-HOST/` | Public search |
| `http://YOUR-SURF-HOST/redactie/` | Redactie (login = api_key) |

Open SURF firewall **port 80** (and 443 if you add TLS later).

## Path C — no extab on SURF (Postgres dump)

**On your laptop** (after local import):

```bash
./scripts/export_demo_db.sh raa_demo.dump
scp raa_demo.dump user@surf:~/raa_modernized/
```

**On SURF:**

```bash
./scripts/restore_demo_db.sh raa_demo.dump
./scripts/surf_stack.sh build-ui
./scripts/surf_stack.sh up
```

## Path A — dev UIs on host (three ports)

If you prefer Vite dev servers during setup/debug:

```bash
./scripts/surf_stack.sh setup
./scripts/surf_stack.sh up-dev
# separate terminals:
cd web/ui && npm run dev -- --host 0.0.0.0 --port 5173
cd web/admin && npm run dev -- --host 0.0.0.0 --port 5174
```

Set `cors_origins` in `config.local.toml` to `:5173` and `:5174` (see `config.surf.toml.example` comments).

Open firewall ports **5173**, **5174**, **8000**.

## Commands reference

| Command | Action |
|---------|--------|
| `./scripts/surf_stack.sh setup` | Copy `config.surf.toml.example` + `data_manifest.surf.toml.example` |
| `./scripts/surf_stack.sh build-ui` | `npm ci` + build ui + admin (`/redactie` base) |
| `./scripts/surf_stack.sh import` | Docker one-shot `import_release.py` |
| `./scripts/surf_stack.sh up` | db + api + nginx (:80) |
| `./scripts/surf_stack.sh up-dev` | db + api only |
| `./scripts/surf_stack.sh down` | Stop compose stack |
| `./scripts/surf_stack.sh status` | Health + URLs |
| `./scripts/export_demo_db.sh` | pg_dump (laptop) |
| `./scripts/restore_demo_db.sh` | pg_restore (SURF) |

## Config files

| File | Purpose |
|------|---------|
| [`config.surf.toml.example`](../config.surf.toml.example) | SURF `config.local.toml` template |
| [`data_manifest.surf.toml.example`](../data_manifest.surf.toml.example) | extab path on `/data` |
| [`web/docker-compose.surf.yml`](../web/docker-compose.surf.yml) | db, api, nginx, import |
| [`web/nginx/surf.conf`](../web/nginx/surf.conf) | `/` ui, `/redactie/` admin, `/api/` proxy |

## VM sizing

| RAM | Use |
|-----|-----|
| 4 GB | Runtime after import (tight) |
| 8 GB | Import in Docker (recommended) |

Ubuntu 22.04+, Docker + compose plugin. Node 20+ on host for `build-ui` (or build on laptop and copy `web/*/build` directories).

## Keep running after SSH

```bash
tmux new -s raa
./scripts/surf_stack.sh up
# Ctrl+B D
```

Or use `restart: unless-stopped` in compose (already set for api/nginx).

## Security (internal pilot)

- Restrict SURF security group to institute IPs / VPN.
- Strong `[editorial].api_key`; share out of band.
- Postgres bound to `127.0.0.1:5432` only (not public).
- Not production-grade auth — Milestone D adds deploy hardening.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| CORS on login | `cors_origins` must match browser URL exactly |
| 502 on /api | `docker compose -f web/docker-compose.surf.yml logs api` |
| Admin 404 assets | Rebuild admin with `ADMIN_BASE_PATH=/redactie npm run build` |
| extab not found | `DATA_ENV=researchcloud`, check `data_manifest.local.toml`, `uv run python -m data_io.check` |
| Import OOM | 8 GB VM or use Path C dump |
| `docker compose` broken | Use `docker-compose` package or build API: `docker build -f web/Dockerfile -t raa-api .` |

## Demo meeting

1. Open public UI + redactie on SURF host in two tabs.
2. Follow [EDITORIAL_DEMO.md](EDITORIAL_DEMO.md).
3. Optional: one amendment before the call.

## Checklist

- [ ] `./scripts/surf_stack.sh setup` + edit configs
- [ ] Data: `import` or `restore_demo_db.sh`
- [ ] `./scripts/surf_stack.sh build-ui && ./scripts/surf_stack.sh up`
- [ ] Firewall port 80
- [ ] Share redactie URL + api_key + EDITORIAL_DEMO.md
