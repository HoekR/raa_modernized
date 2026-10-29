"""Consecutive career transitions and aggregate matrices."""

from __future__ import annotations

from typing import Literal

import pandas as pd

from raa_career_patterns.sequences import intervals_overlap

Grain = Literal["functie", "instelling", "office"]


def pairwise_transitions(sequences: pd.DataFrame) -> pd.DataFrame:
    """Emit consecutive dated steps per person.

    Overlapping consecutive pairs are kept with ``skipped_overlap=True`` so
    callers can inspect them; they are excluded from aggregate matrices.
    """
    if sequences.empty:
        return _empty_transitions()

    dated = sequences.loc[sequences["seq_idx"].notna()].copy()
    if dated.empty:
        return _empty_transitions()

    dated = dated.sort_values(
        by=["persoon_id", "seq_idx"], kind="mergesort"
    ).reset_index(drop=True)

    rows: list[dict] = []
    for persoon_id, group in dated.groupby("persoon_id", sort=False):
        items = group.to_dict("records")
        for i in range(len(items) - 1):
            a, b = items[i], items[i + 1]
            overlap = intervals_overlap(
                a.get("van_period"),
                a.get("tot_period"),
                b.get("van_period"),
                b.get("tot_period"),
            )
            date_complete = a.get("tot_period") is not None and b.get("van_period") is not None
            rows.append(
                {
                    "persoon_id": persoon_id,
                    "from_seq_idx": a["seq_idx"],
                    "to_seq_idx": b["seq_idx"],
                    "from_aanstelling_id": a["aanstelling_id"],
                    "to_aanstelling_id": b["aanstelling_id"],
                    "from_functie_id": a["functie_id"],
                    "to_functie_id": b["functie_id"],
                    "from_instelling_id": a["instelling_id"],
                    "to_instelling_id": b["instelling_id"],
                    "from_functie_naam": a.get("functie_naam"),
                    "to_functie_naam": b.get("functie_naam"),
                    "from_instelling_naam": a.get("instelling_naam"),
                    "to_instelling_naam": b.get("instelling_naam"),
                    "from_van": a.get("van"),
                    "from_tot": a.get("tot"),
                    "to_van": b.get("van"),
                    "to_tot": b.get("tot"),
                    "skipped_overlap": overlap,
                    "date_complete": date_complete,
                }
            )

    if not rows:
        return _empty_transitions()
    return pd.DataFrame(rows)


def _grain_columns(grain: Grain) -> tuple[str, str, str, str]:
    if grain == "functie":
        return (
            "from_functie_id",
            "to_functie_id",
            "from_functie_naam",
            "to_functie_naam",
        )
    if grain == "instelling":
        return (
            "from_instelling_id",
            "to_instelling_id",
            "from_instelling_naam",
            "to_instelling_naam",
        )
    if grain == "office":
        return ("from_office", "to_office", "from_office_label", "to_office_label")
    raise ValueError(f"Unknown grain {grain!r}; expected functie|instelling|office")


def _with_office_keys(transitions: pd.DataFrame) -> pd.DataFrame:
    out = transitions.copy()
    out["from_office"] = list(
        zip(
            out["from_functie_id"].tolist(),
            out["from_instelling_id"].tolist(),
            strict=True,
        )
    )
    out["to_office"] = list(
        zip(
            out["to_functie_id"].tolist(),
            out["to_instelling_id"].tolist(),
            strict=True,
        )
    )
    from_fn = out.get("from_functie_naam")
    to_fn = out.get("to_functie_naam")
    from_in = out.get("from_instelling_naam")
    to_in = out.get("to_instelling_naam")
    if from_fn is not None and from_in is not None:
        out["from_office_label"] = [
            f"{f} @ {i}" for f, i in zip(from_fn.tolist(), from_in.tolist(), strict=True)
        ]
        out["to_office_label"] = [
            f"{f} @ {i}" for f, i in zip(to_fn.tolist(), to_in.tolist(), strict=True)
        ]
    else:
        out["from_office_label"] = out["from_office"].map(str)
        out["to_office_label"] = out["to_office"].map(str)
    return out


def aggregate_matrix(
    transitions: pd.DataFrame,
    *,
    grain: Grain = "instelling",
    exclude_overlap: bool = True,
) -> pd.DataFrame:
    """Aggregate transition edge list into count + row-normalized probability."""
    if transitions.empty:
        return _empty_matrix()

    frame = transitions
    if exclude_overlap and "skipped_overlap" in frame.columns:
        frame = frame.loc[~frame["skipped_overlap"]]

    if frame.empty:
        return _empty_matrix()

    if grain == "office":
        frame = _with_office_keys(frame)

    from_col, to_col, from_label, to_label = _grain_columns(grain)
    work = frame[[from_col, to_col]].copy()
    work.columns = ["from_id", "to_id"]
    if from_label in frame.columns and to_label in frame.columns:
        work["from_label"] = frame[from_label].values
        work["to_label"] = frame[to_label].values
    else:
        work["from_label"] = work["from_id"].map(str)
        work["to_label"] = work["to_id"].map(str)

    # For office grain, stringify tuple keys for parquet friendliness.
    if grain == "office":
        work["from_id"] = work["from_id"].map(
            lambda x: f"{x[0]}:{x[1]}" if isinstance(x, tuple) else x
        )
        work["to_id"] = work["to_id"].map(
            lambda x: f"{x[0]}:{x[1]}" if isinstance(x, tuple) else x
        )

    grouped = (
        work.groupby(["from_id", "to_id"], sort=False, dropna=False)
        .agg(
            count=("from_id", "size"),
            from_label=("from_label", "first"),
            to_label=("to_label", "first"),
        )
        .reset_index()
    )
    row_totals = grouped.groupby("from_id", sort=False)["count"].transform("sum")
    grouped["probability"] = grouped["count"] / row_totals
    grouped["grain"] = grain
    return grouped.sort_values(
        by=["count", "from_id", "to_id"],
        ascending=[False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)


def _empty_transitions() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "persoon_id",
            "from_seq_idx",
            "to_seq_idx",
            "from_aanstelling_id",
            "to_aanstelling_id",
            "from_functie_id",
            "to_functie_id",
            "from_instelling_id",
            "to_instelling_id",
            "from_functie_naam",
            "to_functie_naam",
            "from_instelling_naam",
            "to_instelling_naam",
            "from_van",
            "from_tot",
            "to_van",
            "to_tot",
            "skipped_overlap",
            "date_complete",
        ]
    )


def _empty_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["from_id", "to_id", "count", "from_label", "to_label", "probability", "grain"]
    )
