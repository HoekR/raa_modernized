# Editorial layer (Milestone E)

Demo walkthrough for co-workers → [EDITORIAL_DEMO.md](EDITORIAL_DEMO.md).

Redactie-app voor corpuscorrecties **zonder** `raa_convert` opnieuw te draaien. Wijzigingen worden opgeslagen als **amendments** in Postgres (`editorial.*`).

## Apps

| App | Pad | Poort |
|-----|-----|-------|
| Publiek | `web/ui/` | 5173 |
| Redactie | `web/admin/` | 5174 |
| API | `web/api/` | 8000 |

## Config (`config.local.toml`)

```toml
[editorial]
enabled = true
api_key = "jouw-geheime-sleutel"
editor_id = "rik"
cors_origins = ["http://localhost:5174", "http://127.0.0.1:5174"]
```

## Shipped slices

| Slice | Scope |
|-------|--------|
| **E1** | `instelling.toelichting` |
| **E2** | `persoon.opmerkingen`, `aanstelling.opmerkingen` + search/display refresh |
| **E3** | Persoon kernvelden (naam, geboorte/overlijden jaartallen) + validatie |
| **E0** | Import via `raa_staging` + merge; `editorial.conflicts` bij re-import |
| **E5** | In-browser werklijst-grid (bulk persoon correcties) |

### Editable fields

See `web/api/raa_api/editorial_fields.py`.

## Import + merge (E0)

```bash
uv run python scripts/import_release.py
```

Flow:

1. Prepare extab (gate, validate, enrich)
2. Load **`raa_staging.*`**
3. **`merge_release_into_raa`**: detect conflicts vs active amendments → copy staging → `raa.*` → rebuild spans

`editorial.*` is never dropped. Standalone merge:

```bash
uv run python scripts/merge_release.py --release-id dev
```

Conflicts: admin → **Conflicten** (`/conflicts`) — *amendment behouden* or *nieuwe import accepteren*.

## Admin UI

| URL | Purpose |
|-----|---------|
| `/` | Dashboard |
| `/instellingen/{id}` | Toelichting (rich) |
| `/persoon/{id}` | All editable persoon fields |
| `/aanstelling/{id}` | Opmerkingen |
| `/werklijst/personen` | Spreadsheet grid (bulk edit) |
| `/conflicts` | Re-import conflict queue |

Persoon amendments trigger **`refresh_persoon_derived`** (life dates + `search_display`).

### Werklijst grid

1. Open `/werklijst/personen`
2. Plak persoon-ids (komma, spatie of newline) → **Laden**, of gebruik **Excel-import**
3. Bewerk cellen inline; geel = unsaved, blauw = bestaand amendment
4. **Opslaan** → batch amendments API (max 200 rijen in grid, 500 in import)

### Excel / CSV import

| Actie | Endpoint |
|-------|----------|
| Leeg sjabloon | `GET /api/editorial/import/persoon/template.xlsx` |
| Export met ids | `GET …/template.xlsx?ids=1,2,3` (huidige effective waarden) |
| Upload | `POST /api/editorial/import/persoon?dry_run=true\|false` |

Vaste kolommen (blad `werklijst`):

`persoon_id`, `geslachtsnaam`, `voornaam`, `tussenvoegsel`, `geboorte_j`, `geboorte_m`, `geboorte_d`, `overlijden_j`, `overlijden_m`, `overlijden_d`, `opmerkingen`

- Lege cel → geen wijziging
- `-` → veld expliciet leeg
- `.csv` UTF-8 met exact dezelfde kopregel is ook geldig
- **Proefrun** (`dry_run=true`) valideert zonder op te slaan

Kolommen: naamvelden + **geboorte j/m/d** + **overlijden j/m/d** + `opmerkingen`. Alleen exacte datums (geen `*_als_bekend`-labels). Na opslaan: batch-validatie y→m→d, daarna één `refresh_persoon_derived` per persoon (EDTF + search display).

## API

| Method | Path |
|--------|------|
| `GET/POST` | `/api/editorial/amendments` |
| `DELETE` | `/api/editorial/amendments/{id}` |
| `GET` | `/api/editorial/{entity_type}/{entity_id}` |
| `GET` | `/api/editorial/batch/{entity_type}?ids=1,2,3` |
| `POST` | `/api/editorial/amendments/batch` |
| `GET` | `/api/editorial/conflicts` |
| `POST` | `/api/editorial/conflicts/{id}/resolve` |

Header: `X-Editorial-Api-Key` = `[editorial].api_key`

## Tests

```bash
cd web/api && uv run pytest tests/test_editorial.py tests/test_editorial_merge.py tests/test_editorial_batch.py tests/test_editorial_dates.py tests/test_editorial_import.py -q
```
