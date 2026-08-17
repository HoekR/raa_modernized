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

## Future: visual summaries

**Paused for a later milestone.** Opinion for when we revisit:

| Context | Visualization | Rationale |
|---------|---------------|-----------|
| **Personen search** | Small **bar chart** (facets: stand, per-period counts, top functies) | Fast sense of “who is in this result set”; cheap to compute from facet API |
| **Instelling / aanstelling** | **Network or bipartite graph** (institution ↔ people ↔ functions) | High value for institutional RQs; needs curated limits (top-N edges) to stay readable |
| **Default** | None in v1 | Charts must not crowd the results-first layout; slot inside refine drawer or a “Samenvatting” tab |

**Recommendation:** ship D without charts; add a **facet summary bar chart** in the refine drawer as first experiment (reuses facet counts, no new API). Network graph only after we have max-width detail layout and a `/api/.../graph` with sane caps.

---

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
| D-UI-14 | Charts / graphs | now / later | **later** | 2026-08-17 | Bar chart in refine drawer first candidate |
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

