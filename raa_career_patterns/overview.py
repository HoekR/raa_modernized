"""Corpus overview stats for career-pattern exploration."""

from __future__ import annotations

from typing import Any

import pandas as pd


def career_length_hist(sequences: pd.DataFrame) -> pd.DataFrame:
    dated = sequences.loc[sequences["seq_idx"].notna()]
    if dated.empty:
        return pd.DataFrame(columns=["bucket", "n_persons"])
    lens = dated.groupby("persoon_id", sort=False).size()
    buckets = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 10), (11, 10_000)]
    rows = []
    for lo, hi in buckets:
        label = str(lo) if lo == hi else (f"{lo}-{hi}" if hi < 10_000 else f"{lo}+")
        rows.append(
            {
                "bucket": label,
                "n_persons": int(((lens >= lo) & (lens <= hi)).sum()),
            }
        )
    return pd.DataFrame(rows)


def spells_by_era(sequences: pd.DataFrame) -> pd.DataFrame:
    dated = sequences.loc[sequences["seq_idx"].notna()].copy()
    if dated.empty or "van_year" not in dated.columns:
        return pd.DataFrame(columns=["era", "n_spells"])
    bins = [1400, 1500, 1588, 1795, 1813, 1862]
    labels = ["<1500", "1500-1587", "1588-1794", "1795-1812", "1813-1861"]
    dated["era"] = pd.cut(dated["van_year"], bins=bins, right=False, labels=labels)
    counts = dated["era"].value_counts().sort_index()
    return pd.DataFrame({"era": counts.index.astype(str), "n_spells": counts.values})


def top_entities(
    sequences: pd.DataFrame,
    *,
    col: str,
    n: int = 15,
) -> pd.DataFrame:
    dated = sequences.loc[sequences["seq_idx"].notna()]
    if dated.empty or col not in dated.columns:
        return pd.DataFrame(columns=[col, "n_spells"])
    vc = dated.groupby(col, sort=False).size().sort_values(ascending=False).head(n)
    return pd.DataFrame({col: vc.index, "n_spells": vc.values})


def transition_overview(transitions: pd.DataFrame) -> dict[str, Any]:
    if transitions.empty:
        return {
            "n_edges": 0,
            "n_persons": 0,
            "n_overlap_skipped": 0,
            "n_for_matrix": 0,
            "same_instelling_share": float("nan"),
            "same_functie_share": float("nan"),
            "same_office_share": float("nan"),
        }
    kept = (
        transitions.loc[~transitions["skipped_overlap"]]
        if "skipped_overlap" in transitions.columns
        else transitions
    )
    same_i = kept["from_instelling_id"] == kept["to_instelling_id"]
    same_f = kept["from_functie_id"] == kept["to_functie_id"]
    return {
        "n_edges": int(len(transitions)),
        "n_persons": int(transitions["persoon_id"].nunique()),
        "n_overlap_skipped": int(transitions["skipped_overlap"].sum())
        if "skipped_overlap" in transitions.columns
        else 0,
        "n_for_matrix": int(len(kept)),
        "same_instelling_share": float(same_i.mean()) if len(kept) else float("nan"),
        "same_functie_share": float(same_f.mean()) if len(kept) else float("nan"),
        "same_office_share": float((same_i & same_f).mean()) if len(kept) else float("nan"),
    }


def corpus_overview(sequences: pd.DataFrame) -> dict[str, Any]:
    dated = sequences.loc[sequences["seq_idx"].notna()]
    if dated.empty:
        return {
            "n_spells": 0,
            "n_persons": 0,
            "mean_spells": float("nan"),
            "median_spells": float("nan"),
            "n_collapsed_reappoint": 0,
            "van_year_min": None,
            "van_year_max": None,
        }
    lens = dated.groupby("persoon_id", sort=False).size()
    return {
        "n_spells": int(len(dated)),
        "n_persons": int(dated["persoon_id"].nunique()),
        "mean_spells": float(lens.mean()),
        "median_spells": float(lens.median()),
        "n_collapsed_reappoint": int((dated["n_appointments"] > 1).sum())
        if "n_appointments" in dated.columns
        else 0,
        "van_year_min": int(dated["van_year"].min()),
        "van_year_max": int(dated["van_year"].max()),
    }


def format_overview_text(
    sequences: pd.DataFrame,
    transitions: pd.DataFrame,
    *,
    discontinuity_summary: pd.DataFrame | None = None,
) -> str:
    """Human-readable overview for CLI / notebook."""
    corp = corpus_overview(sequences)
    tr = transition_overview(transitions)
    lines = [
        "=== Career corpus (complete offices) ===",
        f"persons={corp['n_persons']:,}  spells={corp['n_spells']:,}  "
        f"mean/median spells={corp['mean_spells']:.2f}/{corp['median_spells']:.0f}",
        f"collapsed reappointments={corp['n_collapsed_reappoint']:,}  "
        f"van_year={corp['van_year_min']}–{corp['van_year_max']}",
        "",
        "=== Transitions ===",
        f"edges={tr['n_edges']:,}  persons_with_edge={tr['n_persons']:,}  "
        f"overlap_skipped={tr['n_overlap_skipped']:,}  matrix_edges={tr['n_for_matrix']:,}",
        f"same_instelling={tr['same_instelling_share']:.1%}  "
        f"same_functie={tr['same_functie_share']:.1%}  "
        f"same_office={tr['same_office_share']:.1%}",
        "",
        "=== Career length ===",
        career_length_hist(sequences).to_string(index=False),
        "",
        "=== Spells by era ===",
        spells_by_era(sequences).to_string(index=False),
        "",
        "=== Coverage density (NOT political importance; selection artifact) ===",
        top_entities(sequences, col="instelling_naam", n=10).to_string(index=False),
        "",
        "=== Functie vocabulary (college membership labels dominate) ===",
        top_entities(sequences, col="functie_naam", n=8).to_string(index=False),
    ]
    if discontinuity_summary is not None and not discontinuity_summary.empty:
        all_rows = discontinuity_summary.loc[
            discontinuity_summary["stratum"] == "all"
        ]
        lines.extend(
            [
                "",
                "=== F-RQ0 (all stratum) ===",
                all_rows[
                    [
                        "window_label",
                        "n_persons_in_window",
                        "n_crossers",
                        "crosser_rate",
                        "same_instelling_rate",
                        "layer_same_rate",
                    ]
                ].to_string(index=False),
            ]
        )
    return "\n".join(lines)
