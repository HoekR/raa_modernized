# RAA hosting handoff — architecture for colleagues

**Audience:** coworkers who need to understand *what* we run, *where*, and *what is / isn’t* production-ready.  
**Status:** internal pilot / demo (SURF Research Cloud). Production deploy is **Milestone D** (planned, not shipped).  
**Last updated:** 2026-10-29

Related ops docs: [SURF_DEMO.md](SURF_DEMO.md) · [START.md](START.md) · [EDITORIAL.md](EDITORIAL.md) · [DATA.md](DATA.md)

---

## 1. One-paragraph summary

RAA Modernized is a **search + detail web app** over the Repertorium Ambtenaren & Ambtsdragers corpus, plus a small **redactie** UI for editorial amendments. The runtime is intentionally small: **PostgreSQL + FastAPI + static SvelteKit UIs behind nginx**. There is no Elasticsearch, no Kubernetes, and no multi-tenant SaaS layer. A shared pilot already runs on a SURF VM behind institute firewall rules; production hardening (TLS, managed DB, real auth) is still ahead.

---

## 2. What users see

| Surface | Role | Auth today |
|---------|------|------------|
| **Public search UI** | Persons, appointments, institutions, functions — search, facets, detail | None (read-only) |
| **Redactie** (`/redactie/`) | Edit toelichting / person & appointment fields; werklijst; Excel import | Shared **API key** (pilot only) |
| **API** (`/api/…`) | JSON for both UIs | Public read; write routes gated by API key |

Pilot demo host (example): `http://145.38.193.71/` — see [SURF_DEMO.md](SURF_DEMO.md).

---

## 3. Architecture (runtime)

```text
Browser
   │
   ▼
nginx :80
   ├── /           → static public UI  (SvelteKit build)
   ├── /redactie/  → static admin UI   (SvelteKit build, base path /redactie)
   └── /api/       → proxy → FastAPI :8000
                              │
                              ▼
                         PostgreSQL 16
                         schemas: raa.*  (corpus)
                                   editorial.*  (amendments; survives re-import)
```

| Component | Tech | Notes |
|-----------|------|--------|
| DB | Postgres 16 (Docker volume) | Search + facets + detail; ~20k persons / ~50k appointments |
| API | FastAPI (`web/api`) | SQL search; editorial overlay = amendment ?? base |
| Public UI | SvelteKit → static | Built once; served by nginx |
| Redactie | SvelteKit → static | Same pattern; API key login |
| Import | One-shot Docker / `import_release.py` | `extab.pkl` → staging → merge into `raa.*` |

**Not in the hosting path:** Elasticsearch, Redis, message queues, object storage for the app itself, career-patterns research notebooks (local/lab only).

---

## 4. Data flow (what ops people care about)

```text
extab.pkl  ──import──►  raa_staging  ──merge──►  raa.*
                                              ▲
editorial.amendments ─────────────────────────┘  (kept across re-import;
                                                  conflicts logged if base drifts)
```

- **Canonical corpus input:** logical dataset `raa_extab` (`extab.pkl`), registered in `data_manifest.toml` — no hardcoded absolute paths in pipeline code.
- **Re-import** refreshes base tables; editorial rows are preserved; drift can create `editorial.conflicts`.
- **Pilot without extab on the VM:** dump/restore path (`export_demo_db.sh` / `restore_demo_db.sh`) — see SURF “Path C”.

---

## 5. How we host today (SURF pilot)

| Item | Choice |
|------|--------|
| Platform | SURF Research Cloud VM (Ubuntu + Docker) |
| Entry script | `./scripts/surf_stack.sh` (`up` / `down` / `status` / `import` / `build-ui`) |
| Compose file | `web/docker-compose.surf.yml` |
| Public port | **80** only (UI + API via nginx) |
| Postgres port | **127.0.0.1:5432** only (not exposed to the internet) |
| Process model | Containers `restart: unless-stopped` — survive SSH disconnect |
| Sizing | **8 GB RAM** recommended for import; **4 GB** can run after load |
| Network | Firewall / security group restricted to institute IPs or VPN |

**Day-2 ops burden (pilot):** start/stop via one script; rebuild UI when front-end changes; re-import or restore dump when corpus updates; rotate editorial API key out of band.

Local laptop stack (dev only): `./scripts/start_app.sh` → API `:8000`, UI `:5173`, redactie `:5174` — [START.md](START.md).

---

## 6. Security posture (honest)

| Topic | Pilot today | Needed for public / production (Milestone D) |
|-------|-------------|-----------------------------------------------|
| Transport | Often HTTP on internal host | TLS (443) + HSTS |
| Public read | Open to whoever can reach the host | Same, or auth if policy requires |
| Editorial write | Shared API key | Real accounts / IdP; audit trail already partly in amendments |
| DB | Bound to localhost in compose | Managed Postgres + secrets manager |
| Secrets | `config.local.toml` on disk (gitignored) | Injected env / vault |
| HTML content | Sanitized in places (`nh3`); more review before wide public | Content-security policy, full sanitize pass |
| Backups | Docker volume + optional `pg_dump` | Scheduled backups + restore drill |

**Bottom line for worried stakeholders:** the pilot is fine for **restricted institute demos**. It is **not** yet a hardened public production deployment. That is explicitly Milestone **D** in [PLAN.md](../PLAN.md).

---

## 7. Common worries — short answers

**“Is this a big / fragile stack?”**  
No. Four containers (db, api, nginx, optional import). No ES cluster. Static front-ends.

**“Who keeps it up?”**  
Pilot: project team via `surf_stack.sh`. Production: still to be decided with institute hosting (managed Postgres + reverse proxy is the intended shape).

**“What if the VM dies?”**  
Postgres lives in a Docker volume; we can rebuild from `extab` import or from a `pg_dump`. Front-ends rebuild from git. Editorial amendments live in Postgres — back them up with the DB.

**“Can Huygens / IT host this later?”**  
Yes in principle: any Linux host with Docker (or managed Postgres + container/API + static files behind nginx/Apache). No proprietary PaaS lock-in.

**“Does search need Elasticsearch?”**  
Not for current scale. Pilot decision: Postgres facets/search are enough (~20k persons). ES remains an option only if latency/ranking demands it later.

**“Does editorial overwrite the corpus?”**  
No. Base data stays in `raa.*`; edits are amendments. Re-import merges without discarding editorial state (conflicts surface for review).

**“Is the career-patterns research part of hosting?”**  
No. That is a separate Python lab (`raa_career_patterns/`, parquet under scratch). Not required for the web app.

---

## 8. What “good enough for production” still needs (Milestone D sketch)

1. TLS termination and public hostname  
2. Managed or backed-up Postgres (not only a single VM volume)  
3. Stronger editorial auth than a shared API key  
4. Hardened config (no default DB passwords in compose examples)  
5. CI smoke against a staging environment  
6. Explicit backup/restore runbook owned by the host org  

Until then, treat SURF as a **demo / closed pilot**.

---

## 9. Quick reference — commands (SURF)

```bash
./scripts/surf_stack.sh setup      # once: copy config templates
./scripts/surf_stack.sh import     # load extab (or use restore_demo_db.sh)
./scripts/surf_stack.sh build-ui   # static UI + redactie
./scripts/surf_stack.sh up         # db + api + nginx :80
./scripts/surf_stack.sh status
./scripts/surf_stack.sh down       # stop; volume kept
```

Full checklist and troubleshooting: [SURF_DEMO.md](SURF_DEMO.md).

---

## 10. Contact / ownership (fill in before sharing)

| Role | Name | Notes |
|------|------|-------|
| Product / content | | Corpus + editorial policy |
| App / deploy | | This repo + SURF VM |
| Hosting / network | | Firewall, DNS, TLS later |

Repo: `raa_modernized` (bootstrap from `dighum_web_template`; RAA-specific decisions in `PLAN.md` + `docs/MIGRATION_LOG.md`).
