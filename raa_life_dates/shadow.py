"""Shadow life-year inference from aanstelling spans (datamangler port)."""

from __future__ import annotations

import pandas as pd

from raa_life_dates.edtf import derive_life_edtf

BIRTH_OFFSET_YEARS = 34
DEATH_PADDING_YEARS = 22


def _appointment_year_bounds(aanstelling: pd.DataFrame) -> pd.DataFrame:
    grouped = aanstelling.groupby("persoon_id", dropna=False)
    rows: list[dict] = []
    for persoon_id, frame in grouped:
        years: list[int] = []
        for col in ("van", "tot"):
            if col not in frame.columns:
                continue
            for value in frame[col]:
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    continue
                try:
                    years.append(int(pd.Period(str(value), freq="D").year))
                except (ValueError, TypeError):
                    continue
        if not years:
            continue
        rows.append({"persoon_id": persoon_id, "aanst_min_year": min(years), "aanst_max_year": max(years)})
    if not rows:
        return pd.DataFrame(columns=["persoon_id", "aanst_min_year", "aanst_max_year"])
    return pd.DataFrame(rows)


def _source_label(recorded: int | None, effective: int | None, shadow_used: bool) -> str | None:
    if recorded is not None:
        return "recorded"
    if shadow_used and effective is not None:
        return "shadow"
    if effective is not None:
        return "partial"
    return None


def enrich_persoon_life_dates(
    persoon: pd.DataFrame,
    aanstelling: pd.DataFrame,
    *,
    birth_offset_years: int = BIRTH_OFFSET_YEARS,
    death_padding_years: int = DEATH_PADDING_YEARS,
) -> pd.DataFrame:
    """Add EDTF + life year columns to a copy of the persoon frame."""
    result = persoon.copy()
    spans = _appointment_year_bounds(aanstelling)

    edtf_cols = result.apply(derive_life_edtf, axis=1, result_type="expand")
    edtf_cols.columns = ["geboorte_edtf", "overlijden_edtf", "geboorte_year", "overlijden_year"]
    for col in edtf_cols.columns:
        result[col] = edtf_cols[col]

    if not spans.empty:
        result = result.merge(spans, left_on="id", right_on="persoon_id", how="left")
        result = result.drop(columns=["persoon_id"], errors="ignore")
    else:
        result["aanst_min_year"] = pd.NA
        result["aanst_max_year"] = pd.NA

    life_start: list[int | None] = []
    life_end: list[int | None] = []
    life_start_src: list[str | None] = []
    life_end_src: list[str | None] = []
    life_start_edtf: list[str | None] = []
    life_end_edtf: list[str | None] = []

    for row in result.itertuples(index=False):
        geboorte_year = getattr(row, "geboorte_year", None)
        if geboorte_year is not None and pd.notna(geboorte_year):
            geboorte_year = int(geboorte_year)
        else:
            geboorte_year = None

        overlijden_year = getattr(row, "overlijden_year", None)
        if overlijden_year is not None and pd.notna(overlijden_year):
            overlijden_year = int(overlijden_year)
        else:
            overlijden_year = None

        aanst_min = getattr(row, "aanst_min_year", None)
        aanst_max = getattr(row, "aanst_max_year", None)
        if aanst_min is not None and pd.notna(aanst_min):
            aanst_min = int(aanst_min)
        else:
            aanst_min = None
        if aanst_max is not None and pd.notna(aanst_max):
            aanst_max = int(aanst_max)
        else:
            aanst_max = None

        start_year = geboorte_year
        start_shadow = False
        if start_year is None and aanst_min is not None:
            start_year = aanst_min - birth_offset_years
            start_shadow = True

        end_year = overlijden_year
        end_shadow = False
        if end_year is None and aanst_max is not None:
            end_year = aanst_max + death_padding_years
            end_shadow = True
        if start_year is not None and end_year is not None and end_year <= start_year and aanst_max is not None:
            end_year = aanst_max + death_padding_years
            end_shadow = True

        life_start.append(start_year)
        life_end.append(end_year)
        life_start_src.append(_source_label(geboorte_year, start_year, start_shadow))
        life_end_src.append(_source_label(overlijden_year, end_year, end_shadow))

        geb_edtf = getattr(row, "geboorte_edtf", None)
        ovl_edtf = getattr(row, "overlijden_edtf", None)
        if start_shadow and start_year is not None:
            life_start_edtf.append(f"{start_year}~")
        else:
            life_start_edtf.append(geb_edtf if geb_edtf is not None and not pd.isna(geb_edtf) else None)
        if end_shadow and end_year is not None:
            life_end_edtf.append(f"{end_year}~")
        else:
            life_end_edtf.append(ovl_edtf if ovl_edtf is not None and not pd.isna(ovl_edtf) else None)

    result["life_start_year"] = life_start
    result["life_end_year"] = life_end
    result["life_start_source"] = life_start_src
    result["life_end_source"] = life_end_src
    result["life_start_edtf"] = life_start_edtf
    result["life_end_edtf"] = life_end_edtf
    result = result.drop(columns=["aanst_min_year", "aanst_max_year"], errors="ignore")
    return result
