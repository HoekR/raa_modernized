"""Circulation inside a historian-chosen dense institutional subgraph, by era."""

from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

# Dense subgraph v0: Generaliteit core + provincial GS + admiralties.
# Chosen for politics/influence circuits — not top-N volume alone.
_DENSE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"staten[\s\-]*generaal", re.I),
    re.compile(r"raad\s+van\s+sta", re.I),
    re.compile(r"generaliteitsrekenkamer", re.I),
    re.compile(r"gedeputeerde\s+staten", re.I),
    re.compile(r"gecommitteerde\s+raden", re.I),
    re.compile(r"admiraliteit", re.I),
)

# Eras bracket political breakpoints (incl. Rampjaar 1672).
POLITICAL_ERA_BINS = [1400, 1572, 1618, 1651, 1672, 1713, 1795, 1813, 1862]
POLITICAL_ERA_LABELS = [
    "<1572",
    "1572–1617",
    "1618–1650",
    "1651–1671",
    "1672–1712",
    "1713–1794",
    "1795–1812",
    "1813–1861",
]


def in_dense_subgraph(instelling_naam: object) -> bool:
    if instelling_naam is None or (isinstance(instelling_naam, float) and pd.isna(instelling_naam)):
        return False
    text = str(instelling_naam).strip()
    if not text:
        return False
    return any(p.search(text) for p in _DENSE_PATTERNS)


def dense_node_label(instelling_naam: object) -> str:
    """Collapse name variants into coarse circuit nodes for readable tables."""
    if not in_dense_subgraph(instelling_naam):
        return "other"
    text = str(instelling_naam)
    if re.search(r"staten[\s\-]*generaal", text, re.I):
        return "Staten-Generaal"
    if re.search(r"raad\s+van\s+sta", text, re.I):
        return "Raad van State"
    if re.search(r"generaliteitsrekenkamer", text, re.I):
        return "Generaliteitsrekenkamer"
    if re.search(r"gedeputeerde\s+staten", text, re.I):
        return "GS (provincial)"
    if re.search(r"gecommitteerde\s+raden", text, re.I):
        return "Gecomm. Raden"
    if re.search(r"admiraliteit", text, re.I):
        return "Admiraliteit"
    return "dense-other"


def _transition_year(transitions: pd.DataFrame) -> pd.Series:
    """Year of the hop: start year of the destination spell when available."""
    if "to_van" in transitions.columns:
        years = pd.to_numeric(
            transitions["to_van"].astype(str).str.slice(0, 4),
            errors="coerce",
        )
        if years.notna().any():
            return years
    # Fallback if only sequences-derived frames lack to_van strings
    return pd.Series([pd.NA] * len(transitions), index=transitions.index, dtype="Float64")


def filter_dense_circulation(
    transitions: pd.DataFrame,
    *,
    exclude_overlap: bool = True,
    both_in_subgraph: bool = True,
) -> pd.DataFrame:
    """Edges that circulate inside (or touch) the dense subgraph."""
    if transitions.empty:
        return transitions.copy()

    frame = transitions
    if exclude_overlap and "skipped_overlap" in frame.columns:
        frame = frame.loc[~frame["skipped_overlap"]]

    from_in = frame["from_instelling_naam"].map(in_dense_subgraph)
    to_in = frame["to_instelling_naam"].map(in_dense_subgraph)
    mask = (from_in & to_in) if both_in_subgraph else (from_in | to_in)
    out = frame.loc[mask].copy()
    out["from_node"] = out["from_instelling_naam"].map(dense_node_label)
    out["to_node"] = out["to_instelling_naam"].map(dense_node_label)
    out["hop_year"] = _transition_year(out)
    return out


def assign_political_era(
    years: pd.Series,
    *,
    bins: Iterable[int] | None = None,
    labels: Iterable[str] | None = None,
) -> pd.Series:
    bins = list(bins) if bins is not None else POLITICAL_ERA_BINS
    labels = list(labels) if labels is not None else POLITICAL_ERA_LABELS
    return pd.cut(years, bins=bins, right=False, labels=labels)


def circulation_by_era(transitions: pd.DataFrame) -> pd.DataFrame:
    """Count dense-subgraph hops per political era (+ share of all matrix edges)."""
    dense = filter_dense_circulation(transitions)
    all_kept = (
        transitions.loc[~transitions["skipped_overlap"]]
        if "skipped_overlap" in transitions.columns
        else transitions
    )
    if dense.empty:
        return pd.DataFrame(
            columns=["era", "n_dense_hops", "n_all_hops", "dense_share", "n_persons"]
        )

    dense = dense.loc[dense["hop_year"].notna()].copy()
    dense["era"] = assign_political_era(dense["hop_year"])
    all_kept = all_kept.copy()
    all_kept["hop_year"] = _transition_year(all_kept)
    all_kept = all_kept.loc[all_kept["hop_year"].notna()]
    all_kept["era"] = assign_political_era(all_kept["hop_year"])

    dense_counts = dense.groupby("era", observed=False).size()
    all_counts = all_kept.groupby("era", observed=False).size()
    persons = dense.groupby("era", observed=False)["persoon_id"].nunique()

    out = pd.DataFrame(
        {
            "era": POLITICAL_ERA_LABELS,
            "n_dense_hops": [int(dense_counts.get(e, 0)) for e in POLITICAL_ERA_LABELS],
            "n_all_hops": [int(all_counts.get(e, 0)) for e in POLITICAL_ERA_LABELS],
            "n_persons": [int(persons.get(e, 0)) for e in POLITICAL_ERA_LABELS],
        }
    )
    out["dense_share"] = out["n_dense_hops"] / out["n_all_hops"].replace(0, pd.NA)
    return out


def top_dense_edges_by_era(
    transitions: pd.DataFrame,
    *,
    n: int = 5,
    use_coarse_nodes: bool = True,
) -> pd.DataFrame:
    """Top from→to edges inside the dense subgraph, per political era."""
    dense = filter_dense_circulation(transitions)
    if dense.empty:
        return pd.DataFrame(columns=["era", "from_node", "to_node", "count", "rank"])

    dense = dense.loc[dense["hop_year"].notna()].copy()
    dense["era"] = assign_political_era(dense["hop_year"])
    from_col = "from_node" if use_coarse_nodes else "from_instelling_naam"
    to_col = "to_node" if use_coarse_nodes else "to_instelling_naam"

    parts: list[pd.DataFrame] = []
    for era, group in dense.groupby("era", observed=False):
        counts = (
            group.groupby([from_col, to_col], sort=False)
            .size()
            .sort_values(ascending=False)
            .head(n)
            .reset_index(name="count")
        )
        if counts.empty:
            continue
        counts.insert(0, "era", str(era))
        counts["rank"] = range(1, len(counts) + 1)
        counts = counts.rename(columns={from_col: "from_node", to_col: "to_node"})
        parts.append(counts)

    if not parts:
        return pd.DataFrame(columns=["era", "from_node", "to_node", "count", "rank"])
    return pd.concat(parts, ignore_index=True)


def node_flow_by_era(transitions: pd.DataFrame) -> pd.DataFrame:
    """Per era: inbound/outbound hop counts for each coarse dense node."""
    dense = filter_dense_circulation(transitions)
    if dense.empty:
        return pd.DataFrame(columns=["era", "node", "outbound", "inbound", "net"])

    dense = dense.loc[dense["hop_year"].notna()].copy()
    dense["era"] = assign_political_era(dense["hop_year"])

    out_rows: list[dict] = []
    nodes = sorted(set(dense["from_node"]) | set(dense["to_node"]))
    for era, group in dense.groupby("era", observed=False):
        outbound = group.groupby("from_node").size()
        inbound = group.groupby("to_node").size()
        for node in nodes:
            o = int(outbound.get(node, 0))
            i = int(inbound.get(node, 0))
            out_rows.append(
                {
                    "era": str(era),
                    "node": node,
                    "outbound": o,
                    "inbound": i,
                    "net": i - o,
                }
            )
    return pd.DataFrame(out_rows)
