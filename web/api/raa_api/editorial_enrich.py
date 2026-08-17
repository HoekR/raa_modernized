"""Recompute derived persoon columns after editorial amendments."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from raa_api.editorial import apply_effective_value
from raa_api.editorial_fields import EDITABLE_FIELDS
from raa_life_dates.shadow import enrich_persoon_life_dates
from raa_search_display.shadow import enrich_persoon_search_display

_DERIVED_COLS = (
    "geboorte_edtf",
    "overlijden_edtf",
    "geboorte_year",
    "overlijden_year",
    "life_start_year",
    "life_end_year",
    "life_start_edtf",
    "life_end_edtf",
    "life_start_source",
    "life_end_source",
    "search_display",
)


def _effective_persoon_dict(db: Session, persoon_id: int) -> dict[str, Any] | None:
    row = db.execute(
        text("SELECT * FROM raa.persoon WHERE id = :id"),
        {"id": persoon_id},
    ).mappings().first()
    if not row:
        return None
    result = dict(row)
    for field in EDITABLE_FIELDS.get("persoon", {}):
        base = result.get(field)
        effective, amended = apply_effective_value(db, "persoon", persoon_id, field, base)
        if amended:
            result[field] = effective
    return result


def refresh_persoon_derived(db: Session, persoon_id: int, *, commit: bool = True) -> bool:
    """Re-run life-date + search_display enrichment for one person."""
    person = _effective_persoon_dict(db, persoon_id)
    if person is None:
        return False

    conn = db.connection()
    persoon_df = pd.DataFrame([person])
    aanst = pd.read_sql(
        text("SELECT * FROM raa.aanstelling WHERE persoon_id = :id"),
        conn,
        params={"id": persoon_id},
    )
    alias = pd.read_sql(
        text("SELECT * FROM raa.alias WHERE persoon_id = :id"),
        conn,
        params={"id": persoon_id},
    )
    adel = pd.read_sql(text("SELECT * FROM raa.adellijke_titel"), conn)
    acad = pd.read_sql(text("SELECT * FROM raa.academische_titel"), conn)

    enriched = enrich_persoon_life_dates(persoon_df, aanst)
    enriched = enrich_persoon_search_display(enriched, alias, adel, acad)
    row = enriched.iloc[0]

    sets = ", ".join(f"{col} = :{col}" for col in _DERIVED_COLS)
    params = {col: row.get(col) for col in _DERIVED_COLS}
    params["id"] = persoon_id
    db.execute(
        text(f"UPDATE raa.persoon SET {sets} WHERE id = :id"),
        params,
    )
    if commit:
        db.commit()
    return True
