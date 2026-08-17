# RAA SvelteKit UI (Milestone C)

Companion to the static HTML pilot in `web/frontend/static/`. Talks to the FastAPI app on `:8000` via Vite proxy.

**Requires Node ≥ 18.13** (SvelteKit 2).

## Run

```bash
# terminal 1 — API + Postgres
./scripts/dev.sh

# terminal 2 — UI
cd web/ui
npm install
npm run dev
```

Open http://127.0.0.1:5173

## Status

| Slice | Scope | Status |
|-------|-------|--------|
| **C1** | Scaffold + home | done |
| **C2** | Four contexts + period + chips + A–Z | **done** |
| **C3** | Detail pages in SvelteKit | open |
| **C4** | Retire static pilot | open |

Until C3, result rows link to the static pilot detail pages.
