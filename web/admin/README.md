# RAA editorial admin (`web/admin`)

Separate SvelteKit app for **corpus redactie** (Milestone E). Task-oriented editing — not a clone of the public search UI (`web/ui/`).

Full architecture, API, and import/merge: [docs/EDITORIAL.md](../../docs/EDITORIAL.md) · team demo: [docs/EDITORIAL_DEMO.md](../../docs/EDITORIAL_DEMO.md)

## Prerequisites

1. Postgres + API running (from repo root):

   ```bash
   ./scripts/dev.sh    # :8000
   ```

2. Root **`config.local.toml`** (copy from [`config.local.toml.example`](../../config.local.toml.example)):

   ```toml
   [editorial]
   enabled = true
   api_key = "your-secret"
   editor_id = "your-name"
   cors_origins = ["http://localhost:5174", "http://127.0.0.1:5174"]
   ```

3. Node deps (once):

   ```bash
   cd web/admin && npm install
   ```

## Run

```bash
cd web/admin && npm run dev   # http://localhost:5174
npm run check                 # svelte-check
```

Log in at `/login` with the same string as `[editorial].api_key`.

Public UI for verification: `cd web/ui && npm run dev` → http://localhost:5173

## Routes

| URL | Purpose |
|-----|---------|
| `/` | Dashboard, recent amendments, jump by id |
| `/login` | API key login (stored in localStorage) |
| `/instellingen/{id}` | Toelichting editor (HTML, preview) |
| `/persoon/{id}` | Persoon fields + geboorte/overlijden j/m/d groups |
| `/aanstelling/{id}` | Opmerkingen |
| `/werklijst/personen` | Spreadsheet grid + Excel/CSV import |
| `/conflicts` | Re-import conflict queue |
| `/zoeken` | Open record by id (legacy shortcut) |

Entity routes use API names: `persoon`, `aanstelling` (not `personen`).

## Shipped (E0–E5)

| Slice | What |
|-------|------|
| E1 | `instelling.toelichting` |
| E2 | `persoon` / `aanstelling` opmerkingen |
| E3 | Persoon name + exact date parts (j/m/d) |
| E0 | Staging merge; conflicts after re-import |
| E5 | Werklijst grid + `raa_persoon_werklijst.xlsx` template |

Amendments live in Postgres `editorial.*` and survive `import_release.py`.

## Layout

| Path | Role |
|------|------|
| `src/lib/auth.ts` | API key in localStorage |
| `src/lib/editorial.ts` | Fetch helpers → `/api/editorial/*` |
| `src/routes/werklijst/personen/` | Grid + Excel import UI |
| `@raa/shared` | Shared fetch (`web/shared/`, alias in `svelte.config.js`) |

## Common issues

| Problem | Fix |
|---------|-----|
| Login / CORS error | API on `:8000`; `cors_origins` includes `:5174` |
| 503 on editorial API | `[editorial].enabled = true` |
| Changes not on public site | Hard refresh; check dashboard history |
