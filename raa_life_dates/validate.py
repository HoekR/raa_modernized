"""Plausibility bounds for recorded life years in the RAA corpus (1428–1861)."""

from __future__ import annotations

from typing import Any

import pandas as pd

# Inclusive bounds for explicit geboorte/overlijden years (small margin outside corpus).
LIFE_YEAR_MIN = 1400
LIFE_YEAR_MAX = 1920

_GEBOORTE_SOURCE_COLS = (
    "geboortedatum",
    "geboortejaar",
    "geboortemaand",
    "geboortedag",
    "geboortedatum_als_bekend",
    "onbepaaldgeboortedatum",
)

_OVERLIJDEN_SOURCE_COLS = (
    "overlijdensdatum",
    "overlijdensjaar",
    "overlijdensmaand",
    "overlijdensdag",
    "overlijdensdatum_als_bekend",
    "onbepaaldoverlijdensdatum",
)


def is_plausible_life_year(year: int | None) -> bool:
    if year is None:
        return False
    return LIFE_YEAR_MIN <= year <= LIFE_YEAR_MAX


def coerce_plausible_life_year(year: int | None) -> int | None:
    if year is None or not is_plausible_life_year(year):
        return None
    return year


def _parse_year_from_iso(value: Any) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nat", "none"}:
        return None
    try:
        return int(pd.Period(text, freq="D").year)
    except (ValueError, TypeError):
        return None


def _parse_year_field(year_text: Any) -> int | None:
    if year_text is None or (isinstance(year_text, float) and pd.isna(year_text)):
        return None
    try:
        return int(float(str(year_text).strip().replace(".0", "")))
    except ValueError:
        return None


def raw_recorded_geboorte_year(row: pd.Series) -> int | None:
    """Parse geboorte source fields without plausibility filter (for audit)."""
    year = _parse_year_from_iso(row.get("geboortedatum"))
    if year is not None:
        return year
    return _parse_year_field(row.get("geboortejaar"))


def raw_recorded_overlijden_year(row: pd.Series) -> int | None:
    """Parse overlijden source fields without plausibility filter (for audit)."""
    year = _parse_year_from_iso(row.get("overlijdensdatum"))
    if year is not None:
        return year
    return _parse_year_field(row.get("overlijdensjaar"))


def recorded_life_years_from_row(row: pd.Series) -> tuple[int | None, int | None]:
    return raw_recorded_geboorte_year(row), raw_recorded_overlijden_year(row)


def sanitize_implausible_recorded_dates(persoon: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clear source date fields when they parse outside corpus bounds."""
    stats = {"geboorte_cleared": 0, "overlijden_cleared": 0}
    if persoon.empty:
        return persoon, stats

    result = persoon.copy()
    for idx, row in result.iterrows():
        geb, ovl = recorded_life_years_from_row(row)
        if geb is not None and not is_plausible_life_year(geb):
            for col in _GEBOORTE_SOURCE_COLS:
                if col in result.columns:
                    result.at[idx, col] = pd.NA
            stats["geboorte_cleared"] += 1
        if ovl is not None and not is_plausible_life_year(ovl):
            for col in _OVERLIJDEN_SOURCE_COLS:
                if col in result.columns:
                    result.at[idx, col] = pd.NA
            stats["overlijden_cleared"] += 1
    return result, stats


def audit_implausible_recorded_dates(persoon: pd.DataFrame) -> list[dict[str, Any]]:
    """List persons with recorded years outside bounds (pre-sanitize)."""
    rows: list[dict[str, Any]] = []
    for _, row in persoon.iterrows():
        geb, ovl = recorded_life_years_from_row(row)
        issues: list[str] = []
        if geb is not None and not is_plausible_life_year(geb):
            issues.append(f"geboorte={geb}")
        if ovl is not None and not is_plausible_life_year(ovl):
            issues.append(f"overlijden={ovl}")
        if not issues:
            continue
        rows.append(
            {
                "id": int(row["id"]),
                "issues": ", ".join(issues),
                "geboorte_als_bekend": row.get("geboortedatum_als_bekend"),
                "overlijden_als_bekend": row.get("overlijdensdatum_als_bekend"),
            }
        )
    return rows
