"""Build functie × instelling span auxiliary tables from aanstelling rows."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _parse_period(value: Any) -> pd.Period | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nat", "none", "nan"}:
        return None
    try:
        return pd.Period(text, freq="D")
    except (ValueError, TypeError):
        return None


def _period_year(value: Any) -> int | None:
    """Extract calendar year; drop implausible appointment years (e.g. 2031)."""
    period = _parse_period(value)
    if period is None:
        return None
    year = int(period.year)
    # Corpus ends 1861; allow a small margin, reject garbage future years.
    if year < 1400 or year > 1900:
        return None
    return year


def sanitize_aanstelling_years(aanstelling: pd.DataFrame) -> pd.DataFrame:
    """Null van/tot (and als_bekend) when the year is outside plausible bounds."""
    if aanstelling.empty:
        return aanstelling
    result = aanstelling.copy()
    for col, label_col in (("van", "van_als_bekend"), ("tot", "tot_als_bekend")):
        if col not in result.columns:
            continue
        years = result[col].map(_period_year)
        bad = result[col].notna() & years.isna()
        if not bad.any():
            continue
        result.loc[bad, col] = pd.NA
        if label_col in result.columns:
            result.loc[bad, label_col] = pd.NA
    return result


def _witness_row(frame: pd.DataFrame, date_col: str, *, pick_min: bool) -> pd.Series | None:
    dated = frame.loc[frame[date_col].notna()].copy()
    if dated.empty:
        return None
    extreme = dated[date_col].min() if pick_min else dated[date_col].max()
    candidates = dated.loc[dated[date_col] == extreme].sort_values("id", kind="mergesort")
    return candidates.iloc[0]


def _span_label(first_year: Any, last_year: Any) -> str | None:
    if first_year is None and last_year is None:
        return None
    left = str(int(first_year)) if first_year is not None and not pd.isna(first_year) else "?"
    right = str(int(last_year)) if last_year is not None and not pd.isna(last_year) else "?"
    return f"{left} – {right}"


def build_functie_instelling_span(
    aanstelling: pd.DataFrame,
    instelling: pd.DataFrame,
) -> pd.DataFrame:
    """One row per (functie_id, instelling_id) with dated span witnesses."""
    if aanstelling.empty:
        return pd.DataFrame(
            columns=[
                "functie_id",
                "instelling_id",
                "instelling_naam",
                "first_van",
                "last_tot",
                "first_year",
                "last_year",
                "first_van_als_bekend",
                "last_tot_als_bekend",
                "first_aanstelling_id",
                "last_aanstelling_id",
                "aanstelling_count",
                "span_label",
            ]
        )

    inst_names = instelling.set_index("id")["naam"].to_dict() if not instelling.empty else {}
    frame = aanstelling.copy()
    frame["van_period"] = frame["van"].map(_parse_period)
    frame["tot_period"] = frame["tot"].map(_parse_period)

    rows: list[dict] = []
    grouped = frame.groupby(["functie_id", "instelling_id"], dropna=False)
    for (functie_id, instelling_id), grp in grouped:
        if pd.isna(functie_id) or pd.isna(instelling_id):
            continue
        first = _witness_row(grp, "van_period", pick_min=True)
        last = _witness_row(grp, "tot_period", pick_min=False)
        first_year = _period_year(first["van"]) if first is not None else None
        last_year = _period_year(last["tot"]) if last is not None else None
        rows.append(
            {
                "functie_id": int(functie_id),
                "instelling_id": int(instelling_id),
                "instelling_naam": inst_names.get(int(instelling_id), ""),
                "first_van": first["van"] if first is not None else None,
                "last_tot": last["tot"] if last is not None else None,
                "first_year": first_year,
                "last_year": last_year,
                "first_van_als_bekend": first.get("van_als_bekend") if first is not None else None,
                "last_tot_als_bekend": last.get("tot_als_bekend") if last is not None else None,
                "first_aanstelling_id": int(first["id"]) if first is not None else None,
                "last_aanstelling_id": int(last["id"]) if last is not None else None,
                "aanstelling_count": int(len(grp)),
                "span_label": _span_label(first_year, last_year),
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(
        ["functie_id", "first_year", "instelling_naam"],
        na_position="last",
        kind="mergesort",
    ).reset_index(drop=True)


def build_functie_attestation(
    span: pd.DataFrame,
    aanstelling: pd.DataFrame,
    instelling: pd.DataFrame,
) -> pd.DataFrame:
    """Corpus-wide first/last dated witnesses per functie_id (rollup)."""
    if aanstelling.empty:
        return pd.DataFrame(
            columns=[
                "functie_id",
                "corpus_first_year",
                "corpus_first_instelling_id",
                "corpus_first_instelling_naam",
                "corpus_first_aanstelling_id",
                "corpus_last_year",
                "corpus_last_instelling_id",
                "corpus_last_instelling_naam",
                "corpus_last_aanstelling_id",
                "instelling_count",
                "aanstelling_count",
            ]
        )

    inst_names = instelling.set_index("id")["naam"].to_dict() if not instelling.empty else {}
    frame = aanstelling.copy()
    frame["van_period"] = frame["van"].map(_parse_period)
    frame["tot_period"] = frame["tot"].map(_parse_period)

    span_counts = (
        span.groupby("functie_id", dropna=False)
        .agg(instelling_count=("instelling_id", "nunique"), aanstelling_count=("aanstelling_count", "sum"))
        .reset_index()
        if not span.empty
        else pd.DataFrame(columns=["functie_id", "instelling_count", "aanstelling_count"])
    )

    rows: list[dict] = []
    for functie_id, grp in frame.groupby("functie_id", dropna=False):
        if pd.isna(functie_id):
            continue
        first = _witness_row(grp, "van_period", pick_min=True)
        last = _witness_row(grp, "tot_period", pick_min=False)
        counts = span_counts.loc[span_counts["functie_id"] == functie_id]
        instelling_count = int(counts["instelling_count"].iloc[0]) if not counts.empty else 0
        aanstelling_count = int(counts["aanstelling_count"].iloc[0]) if not counts.empty else int(len(grp))
        first_iid = int(first["instelling_id"]) if first is not None and not pd.isna(first["instelling_id"]) else None
        last_iid = int(last["instelling_id"]) if last is not None and not pd.isna(last["instelling_id"]) else None
        rows.append(
            {
                "functie_id": int(functie_id),
                "corpus_first_year": _period_year(first["van"]) if first is not None else None,
                "corpus_first_instelling_id": first_iid,
                "corpus_first_instelling_naam": inst_names.get(first_iid, "") if first_iid else None,
                "corpus_first_aanstelling_id": int(first["id"]) if first is not None else None,
                "corpus_last_year": _period_year(last["tot"]) if last is not None else None,
                "corpus_last_instelling_id": last_iid,
                "corpus_last_instelling_naam": inst_names.get(last_iid, "") if last_iid else None,
                "corpus_last_aanstelling_id": int(last["id"]) if last is not None else None,
                "instelling_count": instelling_count,
                "aanstelling_count": aanstelling_count,
            }
        )

    return pd.DataFrame(rows).sort_values("functie_id", kind="mergesort").reset_index(drop=True)
