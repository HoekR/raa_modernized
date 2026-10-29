# Career pattern research questions

Exploratory RQs for `raa_career_patterns` (research lab, not search UI).
Operational notes: [CAREER_PATTERNS.md](CAREER_PATTERNS.md).

**Framing.** This track is about **politics and influence**: how appointment careers encode access to office, continuity of elites, and reconfiguration of power channels — especially across **wetsverzettingen**. Sequence/transition machinery is the substrate; insight comes from RQs about political structure, not from global matrices alone.

**Corpus caveat.** Spell-count rankings of institutions/functies are **coverage density**, not a map of political importance. They partly reflect which bodies RAA selected and edited most fully (post-Revolt colleges dominate). Choose study circuits for historical reasons; use volume only as a sampling frame.

## F-RQ0 — Does wetsverzetting reconfigure channels of political influence?

**Question.** Around known wetsverzetting cuts (especially **1795**, then **1813**), do ordinary careers show a stronger break in **who holds which layer of office** — and weaker **personnel continuity** at high-influence posts — than in quiet windows of similar length?

In plain terms: at regime breaks, do we see more **forced hops** of institutional identity and more **up/down movement between influence layers** (Generaliteit / supra-local / local) than in peacetime decades?

**Influence layers (v0 proxies — refine with historians).**

| Layer | Proxy in RAA |
|-------|----------------|
| **Generaliteit** | Instelling naam ≈ Staten-Generaal / Raad van State / Generaliteit |
| **Supra-local** | `vertegenwoordigend` (namens / bovenlokaal), not Generaliteit |
| **Local** | Neither of the above |

These are **corpus proxies for relative reach of office**, not a full theory of influence (no wealth, faction, or informal power).

**Strata.**

| Stratum | Definition (v0) |
|---------|-----------------|
| **All** | Any dated career in the window |
| **Generaliteit-touch** | Last pre-cut or first post-cut post is Generaliteit-layer |
| **Other** | Crossers with neither side Generaliteit |

**Cuts vs quiet controls.**

Political breakpoints are chosen for historical reasons (not corpus volume). Quiet windows are placed so their ±10y ranges do **not** overlap those cuts.

| Label | Cut year | Window | Role |
|-------|----------|--------|------|
| `cut_1618` | 1618 | 1608–1628 | Maurits / Synod crisis |
| `cut_1651` | 1651 | 1641–1661 | Grote Vergadering |
| `cut_1672` | 1672 | 1662–1682 | Rampjaar |
| `cut_1713` | 1713 | 1703–1723 | Vrede van Utrecht |
| `cut_1795` | 1795 | 1785–1805 | Bataafse omwenteling (regime rupture) |
| `cut_1813` | 1813 | 1803–1823 | Einde Franse tijd |
| `quiet_1690` | 1690 | 1680–1700 | Quiet between 1672 and 1713 |
| `quiet_1760` | 1760 | 1750–1770 | Quiet between 1713 and 1795 |

**Expectation.** 1795/1813 should show strong discontinuity (wars/revolutions + institutional re-keying). 1618 / 1651 / 1672 / 1713 test whether **political** crises without full regime replacement also register in ordinary career continuity.

## Dense-subgraph circulation over time

Cross-institution hops among a **chosen** circuit (not top-N volume): Staten-Generaal, Raad van State, Generaliteitsrekenkamer, Gedeputeerde Staten, Gecommitteerde Raden, Admiraliteiten.

Break down by political eras bracketed by those cuts:

`1572–1617` | `1618–1650` | `1651–1671` | `1672–1712` | `1713–1794` | `1795–1812` | `1813–1861`

API: `circulation_by_era`, `top_dense_edges_by_era`, `node_flow_by_era` in `raa_career_patterns.circulation`. Notebook section **Circulation inside the dense subgraph (over time)**.

**Measures (per window).**

Among persons with ≥1 dated `van` in the window:

1. **Crosser rate** — post both before and after the cut year (`van_year`)
2. Among crossers (last pre-cut vs first post-cut appointment):
   - **Personnel continuity** — same `instelling_id` / `functie_id` / office
   - **Layer move** — rose / fell / same (Generaliteit > supra > local)
3. Compare cut windows vs quiet controls (and Generaliteit-touch vs other)

**Interpretation caveat (D-56).** Spikes at 1795 may be **historical** (real political rupture) *or* **editorial** (new `instelling` rows, no succession FK). F-RQ0 first **locates** where continuity of influence breaks in the data; separating politics from modelling is a follow-up (successor mapping, historian review).

**How to run.**

```bash
uv run python scripts/career_patterns.py discontinuity
# optional: --cuts cut_1795,quiet_1760
```

Notebook: `notebooks/career_patterns_explore.ipynb` (F-RQ0 section).

## Later (not yet)

- F-RQ1 — pathways **into** high-influence offices (who reaches Generaliteit / key colleges?)
- F-RQ2 — stacking influence (concurrent / overlapping posts)
- F-RQ3 — local → supra-local careers as recruitment into politics
- Mobility / path mining / bipartite (Track F5–F7)
