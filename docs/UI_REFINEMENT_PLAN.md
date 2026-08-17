# UI refinement plan — search & detail pages

> **Branch:** `feature/ui-refinement`  
> **Status:** **implemented** — variant D (phase 1 on `feature/ui-refinement`)  
> **Mockups:** open [`web/ui/design-mockups.html`](../web/ui/design-mockups.html) in a browser (includes **Variant D**)

## Problem statement

After C2/C3 (hybrid search + detail pages), the UI works but feels **crowded**:

| Area | Issue |
|------|--------|
| **Search pages** | Basic search, A–Z strip, advanced `<details>`, active filter chips, sort pills, results table, and facet sidebar all compete for attention on one scroll |
| **Detail pages** | Life dates use ad-hoc paragraphs; aanstellingen use card + `<dl>` grids — inconsistent with search result tables |
| **Cross-page** | Personen/aanstellingen have facets + advanced filters; instellingen/functies are simpler — shared chrome should still feel like one product |

## Goals

1. **Less visual noise** — show only what matters; tuck secondary controls into drawers.
2. **Tables everywhere lists belong** — search hits, life dates, aanstellingen rows use the same table language.
3. **Goetgevonden-like chrome** — layout and density inspired by [app.goetgevonden.nl](https://app.goetgevonden.nl); **colour theme stays archiefblauw** for now (not copper).
4. **Results stay visible** — list/table remains on screen; detail opens in a side drawer where possible.
5. **Keep hybrid search** — basic `q` stays prominent; facets stay live; advanced filters remain (D-60), not removed.
6. **Document decisions** — this file is the source of truth.

## Non-goals (this pass)

- Retiring static pilot (C4)
- New API fields or facet dimensions
- **Charts / network graphs** (deferred — see [Future: visual summaries](#future-visual-summaries))
- Mobile-first redesign (responsive improvements OK, not primary driver)

---

## Chosen direction: **Variant D — Goetgevonden hybrid**

Combines user preferences from review (2026-08-17):

| From | Take |
|------|------|
| **Goetgevonden** | Layout density and drawer patterns; **theme = archiefblauw (B)**, not copper |
| **A (drawers)** | Advanced search, facet refinement, and record detail live in **drawers** — not stacked on the main canvas |
| **B (sort + filters)** | **Sort pills** and **facet sidebar** behaviour like B when the refine drawer is open; active filter chips visible when set |
| **Results first** | No section bands (C rejected); results table occupies maximum horizontal space |
| **Detail economy** | Detail drawer / card uses **full content width** (~`max-width: 1400px` or wider than current `1120px`) |

### Search page (personen — canonical)

```
┌──────────────────────────────────────────────────────────────────┐
│ [ Naam…………………… ] [ Zoeken ]     A B C … Z    [ Verfijnen ▾ ]    │  ← minimal bar
├──────────────────────────────────────────────────────────────────┤
│ 847 treffers   sort: Naam↑  Geboren  Overleden        ‹ 1 2 ›   │  ← B-style sort row
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Naam              │  Geboren  │  Overleden                   │ │  ← results always visible
│ │ Aylva, Tjalling   │     1712  │      1757                    │ │
│ └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
         ┌─ Verfijnen drawer (slides from right, over dimmed results) ─┐
         │ Facetten (B sidebar layout)  │  Meer filters (dates, chips) │
         └────────────────────────────────────────────────────────────┘
         ┌─ Detail drawer (row click) ────────────────────────────────┐
         │ Persoon header + inline dates (Geb | Ovl) + aanstellingen table │
         │ “Volledige pagina →”                                       │
         └────────────────────────────────────────────────────────────┘
```

- **Default view:** search input + compact A–Z + results table + sort row only.
- **Verfijnen drawer:** opens from right; inside = B-style facet column + advanced filter fields (dates, typeahead, stand/adel). Live facet counts still update results behind the drawer.
- **Active chips:** shown inline above results only when filters are applied (not an empty chip bar).
- **Preview icon** (eye, no label) next to naam — hover/focus shows **peek card** on the right.
- **Naam link** → full detail page `/personen/{id}`. Click row no longer opens drawer.

Simple pages (instellingen, functies): same shell minus facet drawer content.

### Detail page (full route)

For direct URLs and print/share:

- **Wider layout** — increase `--raa-max` for detail routes (e.g. 1280–1400px).
- **Hero + inline date row** for life dates (geboren | overleden on one line).
- **Aanstellingen → data table** (full width).
- **Secondary blocks in drawers:** aliassen, bronnen, lokaal aanstellingen, long opmerkingen — collapsed by default; primary table visible immediately.

### Date typography (D-UI-9)

Dates currently *look* like a different font because labels use sans uppercase/muted styling while values use `tabular-nums`. Fix:

- Use **one family** (`--raa-font`) for labels and values everywhere.
- Values: `font-variant-numeric: tabular-nums`; labels: normal weight, muted color — **not** monospace, **not** smaller caps on values.
- Estimated dates: same font, `--raa-ink-faint` + tooltip (unchanged semantics).

---

## Layout variants (reference — A/B/C retained for history)

Open the mockup file and toggle **A / B / C / D**. **D is the build target.**

### Variant A — Toolbar + drawer *(partial — drawer pattern)*

See mockups. Adopted: drawer pattern for secondary UI.

### Variant B — Sidebar facets *(partial — sort + facet panel)*

See mockups. Adopted: sort pills + facet list layout inside refine drawer.

### Variant C — Stacked sections *(rejected)*

Explicit bands add scroll height; user prefers results visible without section chrome.

### Variant D — **Goetgevonden hybrid** *(chosen)*

See ASCII above and mockup tab **D** in `design-mockups.html`.

---

## Detail page — shared table patterns

### Life dates → **inline facts row** (under hero)

| Geboren | Overleden | *(optional: Stand)* |
|---------|-----------|---------------------|
| 1712 | 1757 | Adel |

- **One horizontal row** — geboren and overleden side by side (not stacked label/value rows).
- Right-align date values within their cells; unified sans + `tabular-nums` on values (D-UI-9).
- Estimated dates: `--raa-ink-faint` + tooltip (unchanged semantics).

### Aanstellingen → **data table**

| Functie | Instelling | Van | Tot | Namens |
|---------|------------|-----|-----|--------|
| … | … | … | … | … |

- Row links on functie/instelling; “anderen met deze aanstelling” as row action.
- **Opmerkingen:** expandable sub-row (kept in drawer on detail if long).

### Aliassen, bronnen, opmerkingen

- **Drawer sections** on full detail page; included in detail drawer on search page when space is tight.

---

## Visual summaries (D-UI-14) — implementation plan

**Status:** **14a/b/d/e shipped** (2026-08-17). Facet bar charts + movable Samenvatting + year histogram + **graph overview routes**. **14c** network graph spec below — build only after historian sign-off.

### Goal

Give historians a quick read of *what is in the current result set* without leaving the results-first layout. Charts are a **view** over data we already compute for facets — not a new analytics layer.

### Non-goals (v1 — facet charts, shipped)

- Network / bipartite graphs (phase 14c — separate API + caps)
- Instellingen / functies browse pages (no facet API today)

### Non-goals (14d — year histogram, until built)

- Brush/drag range selection v1 (click single year or decade first; drag brush = 14d+)
- Sub-year granularity

### Previously deferred — now phase 14d

- **Time-series / year histogram** (needs one aggregation query per search; see below)

### Data we already have

| Page | Facet dimensions | Limit |
|------|------------------|-------|
| **Personen** | `period`*, `stand`, `adel`, `functie`, `instelling`, `provincie`, `regio`, `lokaal` | Top 20 per dim (`_PERSONEN_FACET_LIMIT`) |
| **Aanstellingen** | `functie`, `instelling`, `stand`, `adel`, `provincie`, `regio`, `lokaal` | Top 20 per dim |
| **Instellingen / functies** | — | none |

\*`period` facet only when `period_mode = overall` (Alle perioden).

Counts are **disjunctive** (same semantics as facet buttons): “if I added this filter, how many hits remain?”

### UX placement

Inside the search toolbar + a **movable floating panel** (not inside Verfijnen):

```
┌─ Search toolbar ────────────────────────────────────────┐
│ [ Zoeken ]  …   [ Samenvatting ] [ Verfijnen ▾ ]        │
└─────────────────────────────────────────────────────────┘

┌─ Samenvatting (floating, draggable) ─────┐
│ ≡ Samenvatting                        ×  │  ← drag header; position remembered per page
│ Periode (Alle perioden only)             │
│ Middeleeuwen  ████████  (teal)           │
│ Republiek     ██████████ (blue)          │
│ … Stand / functie / instelling           │
└──────────────────────────────────────────┘

┌─ Verfijnen drawer ───────────────────────┐
│ Facetten + advanced filters (unchanged)  │
└──────────────────────────────────────────┘
```

**Why movable, not a drawer tab:** historians can keep charts visible beside results while refining filters; position persists for the session.

### Phase 14d — Year histogram (Goetgevonden-like)

**Reference:** [Goetgevonden](https://goetgevonden.nl/) shows a **date histogram** above results; adjusting the histogram narrows the result set (histogram = filter control, not decoration).

**Scope:** personen + aanstellingen only.

**Life-date rules (shadow, exact mode, EDTF filters):** see [LIFE_DATES.md](LIFE_DATES.md) §7–9.

#### What to count

| Page | Recommended axis (v1) | SQL source | Notes |
|------|----------------------|------------|-------|
| **Aanstellingen** | Start year of appointment | `_aanstelling_van_year_sql()` on text `a.van` | One bar per year; unparseable/`None` → `undated` footnote |
| **Personen** | Birth year | `COALESCE(p.geboorte_year, p.life_start_year)` when `include_shadow_dates`; else `p.geboorte_year` | Same rule as geboorte filters — **not** the grey “estimated” display column alone |

**Personen chart title** (must reflect the active date mode — **decided** 2026-08-17):

| `include_shadow_dates` | UI label (Meer filters radio) | Histogram title |
|------------------------|-------------------------------|-----------------|
| `true` (default) | incl. geschatte jaartallen | **Geboortejaar (incl. schatting)** |
| `false` | zoek exacte datums | **Geboortejaar (alleen expliciet vastgelegd)** |

Persons in the result set who have only a shadow birth year (no `geboorte_year`) appear in **`timeline_meta.undated`** when exact mode is on — not distributed across bars. Footnote example: *“318 zonder expliciet vastgelegd geboortejaar (schattingen niet meegeteld).”*

Helper: `birthYearChartTitle()` / `undatedTimelineNote()` in `web/ui/src/lib/yearHistogram.ts`.

**Personen v2 (optional toggle in Samenvatting):** “eerste aanstelling” or “actief in jaar” (count distinct persons with any `a.van` in that year) — closer to document-date histograms but noisier.

#### API (extend search response)

Add to `SearchResponse`:

```python
class YearCount(BaseModel):
    year: int
    count: int

class TimelineMeta(BaseModel):
    field: str          # e.g. "geboorte", "aanstelling_van"
    bin: str = "year"   # "year" | "decade" (auto when span > 120 years)
    undated: int = 0    # hits without a year on this axis
```

```json
"timeline": [{"year": 1750, "count": 42}, …],
"timeline_meta": {"field": "geboorte", "bin": "year", "undated": 318}
```

- Same `SearchRequest` body as search (respects filters, period, shadow dates).
- Computed in `_personen_timeline` / `_aanstelling_timeline` alongside facets (one extra `GROUP BY` per search).
- **Decade bins** when `max(year) - min(year) > 120` (keep ≤ ~20 bars for UI).

#### UI placement (two surfaces)

1. **Compact strip on results canvas** (Goetgevonden-like) — **recommended first**
   - Thin bar chart in `results-meta` (above table, full width of results column).
   - Height ~4–5rem; vertical bars; no labels on every bar (hover `title` + optional range label).
   - **Click bar** → narrow date filter (aanstellingen: set `van`/`tot` to year; personen: set `geboorte` EDTF to `YYYY/YYYY` or `../YYYY`).
   - **Shift+click** second bar → range (14d+ if v1 is single-year only).

2. **Samenvatting panel** — same data, taller chart + axis labels (reuse component).

#### Component sketch

| Component | Role |
|-----------|------|
| `YearHistogram.svelte` | `{ bins, compact?, onselect? }` — CSS or SVG vertical bars |
| `yearHistogram.ts` | Chart titles, undated footnotes; bin scaling for 14d |

No chart library (consistent with D-UI-14d).

### Phase 14e — Graph overview page — **done**

Routes (URL-synced with list search state):

```
/personen/overzicht?q=…&filters=…
/aanstellingen/overzicht?q=…&filters=…
```

| Section | Content |
|---------|---------|
| Header | Query summary + treffer count + **← Terug naar lijst** |
| Primary | Full-height year histogram (same data as results strip) |
| Secondary | Facet bar charts (period, stand, functie, instelling) |
| Footer | Caveats (undated, shadow dates, top-8 facets, shareable URL) |

- **URL-synced** — `searchUrl.ts` encode/decode; overview ↔ list share query string.
- Does **not** replace Samenvatting panel — panel = quick peek; overview = validation / presentation.
- Entry: toolbar link **“Overzicht →”** next to Samenvatting (when `hasSearched`).

Components: `SearchOverview.svelte` + thin route wrappers.

### Chart type (phase 1–2)

**Horizontal bar chart** — one dimension at a time, CSS + `<div>` bars (no chart library).

| Property | Choice |
|----------|--------|
| Bars | `width = count / max(count in chart) × 100%` |
| Labels | Truncate long names; full name in `title` tooltip |
| Max bars | **8** per chart (rest: “+N more in Facetten”) — **except period chart: always 4 bars** |
| Colour | Default `--raa-accent` for stand/functie/instelling charts |
| **Period chart colour** | **One distinct colour per period key** when `period_mode = overall` (see below) |
| Interaction | **Click bar → same as facet toggle** (recommended) |

#### Period bar chart (Alle perioden only)

When the global period selector is **Alle perioden** (`period_mode = overall`), show **Verdeling per periode** at the top of Samenvatting:

- Data: `facets.period[]` (already returned by search API)
- **Fixed order** (matches period dropdown): Middeleeuwen → Republiek → Bataafs-Franse tijd → Negentiende eeuw
- **Four bars**, one per period — no “top 8” truncation; show count `0` as empty/minimal bar or omit with note
- **Distinct fill per `period` key** (archiefblauw-friendly palette; works in archive theme):

| Key | CSS variable | Fill (archive theme) |
|-----|--------------|----------------------|
| `me` | `--raa-period-me` | `#5a8a7a` (muted green) |
| `republiek` | `--raa-period-republiek` | `#2f6f8f` (accent blue) |
| `batfra` | `--raa-period-batfra` | `#b8860b` (amber/gold) |
| `negentiende_eeuw` | `--raa-period-negentiende` | `#5c6b7a` (slate) |

- Labels use facet `label` (includes date range from API)
- **Click bar** → switch to that period (`periodKey.set(key)`) — same as choosing it in the header dropdown / period facet row
- Hidden when a single period is scoped (Republiek, ME, etc.) — the chart would be redundant

**Personen first.** Aanstellingen has no `period` facet today; add in 14b only if we extend `_aanstelling_facets` with the same overall-mode period breakdown.

Alternative considered: view-only bars — rejected; clicking a facet row is already the mental model.

### Phase breakdown

| Phase | Scope | API | Effort |
|-------|--------|-----|--------|
| **14a** | Personen — movable Samenvatting: period (overall) + stand + functie + instelling | reuse `facets` | **done** |
| **14b** | Aanstellingen — movable Samenvatting (functie, instelling, stand) | reuse `facets` | **done** |
| **14d** | Year histogram — API `timeline` + compact results strip + Samenvatting | **new** aggregation on search | ~1 session |
| **14e** | Graph overview page (`/personen/overzicht`, `/aanstellingen/overzicht`) | reuse search + timeline | **done** |
| **14c** | Bipartite / network (institution ↔ person ↔ function) | **new** `POST …/graph` with top-N edges, max 50 nodes | **spec only** — historian review before build |

### Components (new)

| Component | Role |
|-----------|------|
| `MovablePanel.svelte` | Draggable floating panel; session position via `draggablePanel.ts` |
| `SummaryPanel.svelte` | `MovablePanel` + `FacetSummary` for personen / aanstellingen |
| `FacetBarChart.svelte` | Horizontal facet bars (shipped) |
| `PeriodBarChart.svelte` | Four-colour period breakdown (shipped) |
| `FacetSummary.svelte` | Composes facet + timeline charts (shipped / extending) |
| `YearHistogram.svelte` | Vertical bar timeline; compact mode for results strip |
| `yearHistogram.ts` | Bin scaling, decade grouping |

### Empty / edge cases

- **No search yet** — Samenvatting tab disabled or hint: “Zoek eerst”
- **0 hits** — “Geen treffers om samen te vatten”
- **Single facet value** — still show one bar (100%)
- **Period facet** — **multi-colour bar chart** at top of Samenvatting when Alle perioden; fixed 4-bar order; click → scope to that period
- **Adel** — skip as chart (boolean; facet button enough)

### Phase 14c — Network graph (spec — do not build until confirmed)

**Use case (primary):** aanstellingen RQs like P3/A1 — after functie + instelling filters, see *who connected where* in a medium slice (not 677-row tables).

**Default graph shape (proposed):**

| Layer | Choice |
|-------|--------|
| **Nodes** | `person` + `institution` (bipartite) |
| **Edges** | aggregated person↔institution; `weight` = appointment count |
| **Edge label / tooltip** | function name(s), optional van/tot on hover |
| **Toggle (v2)** | collapse to function↔institution summary mode |

**Not v1:** full tripartite person–function–institution (too dense).

**API (proposed):**

```http
POST /api/search/aanstellingen/graph
# same body as search + graph options
{ "limit_edges": 30, "mode": "person_institution" }
```

```json
{
  "nodes": [{ "id": "p:21510", "type": "person", "label": "Aylva, Tj." }],
  "edges": [{ "source": "p:21510", "target": "i:171", "weight": 2, "label": "gedeputeerde" }],
  "meta": { "total_appointments": 677, "shown_edges": 30, "truncated": true }
}
```

Reuse `_aanstelling_where()` — same filter semantics as search.

**UI placement (proposed):** section on **`/aanstellingen/overzicht`** (not Samenvatting panel — needs ~400×400px). Optional later: `/aanstellingen/netwerk`.

**Caps & caveats:**

- Default **30 edges**, hard max **50 nodes**
- Top-N by edge weight; banner: *“Top N verbindingen van M aanstellingen”*
- Consider hiding graph when `total > 500` unless filters tightened

**Interaction (proposed):** click node → apply facet filter (same as bar charts); v1 view-only acceptable if layout time-boxed.

**Rendering (proposed):** d3-force or Cytoscape.js — not pure SVG (layout too hard). Defer library choice until historian validates need.

**Historian decisions still open:**

1. Primary RQ to nail (e.g. A1 with functie+instelling pre-filtered?)
2. Person↔institution vs function↔institution default
3. Click-to-filter vs view-only v1
4. Max `total` before graph is misleading

### Phase 14c sketch (archive — superseded by spec above)

For aanstellingen RQs like “who held office X at institution Y”:

- Input: current search filters + `limit` (default 30 edges)
- Output: `{ nodes: [{id, label, type}], edges: [{source, target, weight}] }`
- Render: lightweight SVG or canvas; defer library choice until 14a/b shipped
- Must show **“top N of M appointments”** caveat (same spirit as entity-span caveats)

### Decision log (to confirm before build)

| ID | Question | Recommendation |
|----|----------|----------------|
| D-UI-14a | Tab vs stacked vs floating | **Floating movable Samenvatting** + Verfijnen for facets only — **decided** 2026-08-17 |
| D-UI-14b | Click bar → filter? | **Yes** — reuse `onFacetToggle` / `periodKey.set` — **decided** 2026-08-17 |
| D-UI-14c | Personen charts first | **Periode (overall) + stand + functie + instelling** — **decided** 2026-08-17 |
| D-UI-14d | Chart library | **None** — CSS bars v1 |
| D-UI-14e | Instellingen/functies | **Skip** until facets exist |
| D-UI-14f | Period chart colours | **One colour per period key** (4-colour palette) — **decided** 2026-08-17 |
| D-UI-14g | Samenvatting placement | **Movable floating panel** (toolbar toggle; drag header; session position) — **decided** 2026-08-17 |
| D-UI-14h | Year histogram axis (personen) | **Birth year** (respect shadow-date flag) — **recommended**; aanstelling-activity = v2 toggle |
| D-UI-14i | Year histogram placement | **Compact strip on results** + duplicate in Samenvatting — **recommended** |
| D-UI-14j | Histogram interaction | **Click year → date filter** (Goetgevonden-like); range brush later |
| D-UI-14k | Overview page | **Separate route** after 14d | **done** — `/personen/overzicht`, `/aanstellingen/overzicht` | 2026-08-17 |
| D-UI-14l | Personen histogram title | **Dynamic label** from date-mode toggle (`incl. schatting` / `alleen expliciet vastgelegd`) — **decided** 2026-08-17 |

### Implementation order (updated)

1. ~~Facet bar charts + movable Samenvatting~~ — **done**
2. ~~**14d** API `timeline` + `YearHistogram` + results strip~~ — **done**
3. ~~**14d** personen birth-year timeline + shadow-date parity~~ — **done**
4. ~~Samenvatting panel: embed same `YearHistogram`~~ — **done**
5. ~~**14e** overview routes~~ — **done**
6. Phase **14c** network graph — **after historian sign-off** on spec above

---

## Future: visual summaries (archive note)

Original one-liner recommendation retained above as **D-UI-14 implementation plan**. Network graph remains phase 14c.

## Component checklist

| Component | Action |
|-----------|--------|
| `Drawer.svelte` | Reusable slide-over (refine, detail, secondary detail sections) |
| `SearchShell.svelte` | Minimal top bar, results slot, drawer triggers |
| `ResultsTable.svelte` | Shared table + sort header row (B-style pills) |
| `LifeDatesRow.svelte` | Inline geboren \| overleden \| stand row on detail + drawer |
| `FactsTable.svelte` | Other detail metadata if needed |
| `AanstellingenTable.svelte` | Detail + search nested rows |
| `DetailDrawer.svelte` | Row-click preview; link to full page |
| `FacetPanel.svelte` | Move into refine drawer; keep B layout inside |
| `app.css` | Archiefblauw default; wider `--raa-max-detail`; unified `.date` typography; `.life-dates` inline row |
| `theme.ts` | Default theme **`archive`** (unchanged) |
| Routes | Refactor all search + detail routes to shell |

---

## Decision log

| ID | Topic | Options | **Choice** | Date | Notes |
|----|-------|---------|------------|------|-------|
| D-UI-1 | Search layout variant | A / B / C / **D hybrid** | **D** | 2026-08-17 | A drawers + B sort/facets |
| D-UI-2 | Facet default state | open / closed / desktop only | **closed (drawer)** | 2026-08-17 | Open via “Verfijnen”; live counts behind drawer |
| D-UI-3 | A–Z placement | inline / band / drawer | **inline compact** | 2026-08-17 | Single row next to search |
| D-UI-4 | Advanced filters | details / drawer / modal | **drawer** | 2026-08-17 | Inside refine drawer with facets |
| D-UI-5 | Detail life dates | facts table / inline row / subtitle | **inline row (Geb \| Ovl same line)** | 2026-08-17 | Wider detail card |
| D-UI-6 | Aanstellingen opmerkingen | expand row / sub-row / drawer | **expand row + drawer for long** | 2026-08-17 | |
| D-UI-7 | Aanstellingen search results | flat / grouped | **grouped** (keep nested) | 2026-08-17 | Flatten later if drawer preview needs it |
| D-UI-8 | Pilot bar in header | keep / shrink / remove | **shrink** | 2026-08-17 | Remove at C4 |
| D-UI-9 | Date typography | mixed / unified tabular sans | **unified sans + tabular-nums on values only** | 2026-08-17 | Fix label/value contrast illusion |
| D-UI-10 | Default colour theme | archive / copper / green | **archive (archiefblauw)** | 2026-08-17 | Goetgevonden layout only; copper optional in switcher |
| D-UI-11 | Detail on search page | navigate / drawer / split | **drawer + full page link** | 2026-08-17 | Results stay visible |
| D-UI-12 | Detail page width | 1120px / wider | **~1400px detail routes** | 2026-08-17 | Economy of horizontal space |
| D-UI-13 | Secondary detail sections | on-page / drawer | **drawer** | 2026-08-17 | Aliassen, bronnen, lokaal, long notes |
| D-UI-14 | Charts / graphs | now / later | **14a/b shipped; 14d/e planned** | 2026-08-17 | Facet bars + movable Samenvatting; year histogram next |
| D-UI-15 | Result hover preview | none / tooltip / peek card | **icon-triggered peek card** | 2026-08-17 | Eye icon beside naam; hover/focus → peek. Naam → full page. |

---

## How to review

1. `open web/ui/design-mockups.html`
2. Select **Variant D**
3. Compare with A/B/C if needed

## Implementation order

1. **Theme + typography** — keep `archive` default, unified `.date` / `.life-dates` inline row, wider detail max-width
2. **`Drawer.svelte` + `ResultsTable.svelte` + `FactsTable.svelte`**
3. **`SearchShell`** — refactor instellingen/functies (simplest)
4. **Personen + aanstellingen** — refine drawer, sort row, detail drawer
5. **Detail routes** — facts table, aanstellingen table, secondary drawers
6. **Cleanup** — dedupe route `<style>` blocks, shrink pilot bar

