"""Institutional corpus gate: dated appointments only, persons via office only."""

from __future__ import annotations

from typing import Any

import pandas as pd


def appointment_van_year(value: Any) -> int | None:
    """Parse appointment start (`van`) to calendar year, or None if undated."""
    return _appointment_year(value)


def appointment_tot_year(value: Any) -> int | None:
    """Parse appointment end (`tot`) to calendar year, or None if open/undated."""
    return _appointment_year(value)


def _appointment_year(value: Any) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() == "none":
        return None
    try:
        return int(pd.Period(text, freq="D").year)
    except (ValueError, TypeError):
        return None


def apply_institutional_date_gate(
    extab: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], dict[str, int]]:
    """Drop undated aanstellingen and persons without any dated appointment.

    RAA is institution-first: every person enters via a dated office record.
    Returns (cleaned extab copy, drop counts).
    """
    stats: dict[str, int] = {
        "aanstelling_undated": 0,
        "persoon_no_dated_aanstelling": 0,
    }
    if "aanstelling" not in extab or "persoon" not in extab:
        return extab, stats

    result = dict(extab)
    aanst = result["aanstelling"].copy()
    dated_mask = aanst["van"].map(appointment_van_year).notna() if "van" in aanst.columns else pd.Series(False, index=aanst.index)
    stats["aanstelling_undated"] = int((~dated_mask).sum())
    aanst = aanst.loc[dated_mask].copy()

    dated_person_ids = set(aanst["persoon_id"].dropna().astype(int).tolist())
    persoon = result["persoon"].copy()
    keep_person = persoon["id"].isin(dated_person_ids)
    stats["persoon_no_dated_aanstelling"] = int((~keep_person).sum())
    persoon = persoon.loc[keep_person].copy()
    aanst = aanst.loc[aanst["persoon_id"].isin(persoon["id"])].copy()

    result["persoon"] = persoon
    result["aanstelling"] = aanst

    kept_ids = set(persoon["id"].tolist())
    for table in ("alias", "bron_details"):
        if table in result and "persoon_id" in result[table].columns:
            frame = result[table]
            before = len(frame)
            result[table] = frame.loc[frame["persoon_id"].isin(kept_ids)].copy()
            stats[f"{table}_orphan"] = before - len(result[table])

    return result, stats
