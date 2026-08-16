"""EDTF interval filters → SQL overlap clauses for personen search."""

from __future__ import annotations

from raa_life_dates.edtf import YearInterval, parse_edtf_interval


def _year_column(kind: str, include_shadow: bool) -> str:
    if kind == "geboorte":
        if include_shadow:
            return "COALESCE(p.geboorte_year, p.life_start_year)"
        return "p.geboorte_year"
    if include_shadow:
        return "COALESCE(p.overlijden_year, p.life_end_year)"
    return "p.overlijden_year"


def life_year_overlap_sql(
    kind: str,
    edtf_value: str,
    *,
    include_shadow: bool,
    param_prefix: str,
) -> tuple[str, dict]:
    """Build SQL for inclusive year overlap against geboorte or overlijden bounds."""
    interval = parse_edtf_interval(edtf_value)
    col = _year_column(kind, include_shadow)
    clauses: list[str] = [f"{col} IS NOT NULL"]
    params: dict = {}

    if interval.start is not None:
        key = f"{param_prefix}_start"
        clauses.append(f"{col} >= :{key}")
        params[key] = interval.start
    if interval.end is not None:
        key = f"{param_prefix}_end"
        clauses.append(f"{col} <= :{key}")
        params[key] = interval.end

    return " AND ".join(clauses), params


def life_span_overlap_sql(
    edtf_value: str,
    *,
    include_shadow: bool,
    param_prefix: str,
) -> tuple[str, dict]:
    """Overlap person life span [life_start_year, life_end_year] with query interval."""
    interval = parse_edtf_interval(edtf_value)
    if include_shadow:
        start_col, end_col = "p.life_start_year", "p.life_end_year"
    else:
        start_col, end_col = "p.geboorte_year", "p.overlijden_year"

    clauses: list[str] = [f"{start_col} IS NOT NULL", f"{end_col} IS NOT NULL"]
    params: dict = {}

    if interval.end is not None:
        key = f"{param_prefix}_q_end"
        clauses.append(f"{start_col} <= :{key}")
        params[key] = interval.end
    if interval.start is not None:
        key = f"{param_prefix}_q_start"
        clauses.append(f"{end_col} >= :{key}")
        params[key] = interval.start

    return " AND ".join(clauses), params
