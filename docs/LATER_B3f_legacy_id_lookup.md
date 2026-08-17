# Later: Silent Legacy-ID Person Lookup (B3f)

## Goal
Allow users (e.g. external bookmarks / legacy systems) to look up persons by a legacy identifier.

Implementation principle: **legacy IDs must not become visible in the normal UI/search experience**. The legacy lookup should be a compatibility shim that redirects to the canonical modern person page.

## Target behavior
1. User requests a legacy URL:
   - Proposed: `/personen/oud/{legacy_id}`
2. Server looks up `legacy_id` in a backend mapping table (personen only).
3. If found, server returns a redirect (HTTP 302/307) to:
   - `/personen/{modern_person_id}`
4. If not found, return `404`.

No legacy ID should be rendered on the destination page, and search results should remain modern-id-only.

## Data sources / id namespaces (important)
There are multiple id spaces in play; the compatibility layer must be explicit about the legacy source:

- Legacy “source” ids may come from different exports/snapshots (e.g. legacy `raa_web`, Huygens public ids, regent orig keys).
- A single numeric value (e.g. `6448`) can refer to **different** persons depending on the namespace.

Therefore, the mapping table must include:
- `legacy_source` (string enum / label)
- `legacy_id` (stored as text or int, depending on source)

## Proposed import pipeline (personen only)

### Step A: build a candidate mapping from `map_personen.tsv`
Start from:
- `nw_raa/convert_raa/map_personen.tsv` (tab-separated)

This file maps:
- `id_old` (raa_web) -> `id_new` (raa_nw)

It includes:
- `confidence` (tiers: `name_date`, `aanstelling`, `needs_review`, `name_only`, `unmatched`)

### Step B: canonicalize Fries/divperioden ids before storing as modern targets
Fries provenance is not a separate UI period; it is encoded as DB flags:
- `divperioden` rows are editorially superseded by `republiek_friezen` rows.

In the pilot import pipeline:
- `import_release.py` purges `divperioden` on core tables (`purge_divperioden()`).

At mapping time, `map_personen.tsv` can land on the *divperioden* variant when a *republiek_friezen* twin exists.

Fix approach:
1. Maintain a divperioden -> republiek_friezen bridge keyed by the shared suffix:
   - `divperioden_{N}` <-> `republiek_friezen_{N}`
2. Before writing final redirects, rewrite any `id_new` that points to a divperioden-only modern id into its corresponding republiek_friezen modern id (when a twin exists).

This canonicalization should be applied when generating the legacy redirect map.

### Step C: confidence policy for which rows to import
Redirects should be conservative: wrong redirects are worse than 404.

Recommended:
- Allow redirects for:
  - `name_date`
  - `aanstelling`
- Do NOT auto-redirect for:
  - `needs_review`
  - `name_only`
  - `unmatched`

Queue those rows for manual review later (optional future improvement).

## Suggested database table
Create a small auxiliary table (no UI surfacing):

- `raa.legacy_persoon_id_map`
  - `legacy_source` (e.g. `raa_web`)
  - `legacy_id` (text)
  - `persoon_id` (modern `raa.persoon.id`)
  - `confidence` (tier)
  - `remap_note` (e.g. `divperioden_308 -> republiek_friezen_308`)
  - primary key: (`legacy_source`, `legacy_id`)

## API & routing
Recommended API endpoint:
- `GET /api/personen/oud/{legacy_id}`
  - returns either:
    - redirect to `/personen/{modern_id}`
    - or JSON `{modern_id}` that the UI/router redirects

SvelteKit route (thin layer) can implement the redirect as well, but the important part is that:
- the mapping lookup is server-side
- no legacy ids appear in normal UI components

## Validation / anchors (to avoid id namespace confusion)
Before turning on for all legacy ids, validate with known anchors:

- Use the validation anchor documented in:
  - `docs/VALIDATION_RQS.md`
  - `docs/MIGRATION_LOG.md`

Example known mapping (documented):
- Huygens legacy `6448` -> pilot modern `21510` (Tjaerd baron van Aylva)

Note: do not assume `map_personen.tsv` numeric ids are interchangeable with Huygens ids. Validate the namespace explicitly.

## Postpone status
This file is a backlog capture. No implementation has started yet.

