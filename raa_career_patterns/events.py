"""Load and normalize aanstelling rows as career events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from raa_entity_spans.spans import sanitize_aanstelling_years

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

PERIOD_FLAG_COLS = (
    "me",
    "republiek",
    "republiek_friezen",
    "batfra",
    "negentiende_eeuw",
    "divperioden",
)

_EVENTS_SQL = """
SELECT
    a.id AS aanstelling_id,
    a.persoon_id,
    a.functie_id,
    a.instelling_id,
    a.van,
    a.tot,
    a.van_als_bekend,
    a.tot_als_bekend,
    a.me,
    a.republiek,
    a.republiek_friezen,
    a.batfra,
    a.negentiende_eeuw,
    a.divperioden,
    a.vertegenwoordigend,
    a.provincie_id,
    a.mark_for_delete,
    f.naam AS functie_naam,
    i.naam AS instelling_naam,
    COALESCE(p.listing_naam, p.search_display) AS persoon_naam
FROM raa.aanstelling a
LEFT JOIN raa.functie f ON f.id = a.functie_id
LEFT JOIN raa.instelling i ON i.id = a.instelling_id
LEFT JOIN raa.persoon p ON p.id = a.persoon_id
WHERE COALESCE(a.mark_for_delete, 0) = 0
"""


def _parse_period(value: Any) -> pd.Period | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text_val = str(value).strip()
    if not text_val or text_val.lower() in {"nat", "none", "nan", "<na>"}:
        return None
    try:
        return pd.Period(text_val, freq="D")
    except (ValueError, TypeError):
        return None


def _period_year(period: pd.Period | None) -> int | None:
    if period is None or (isinstance(period, float) and pd.isna(period)):
        return None
    try:
        if pd.isna(period):
            return None
    except (TypeError, ValueError):
        pass
    year = int(period.year)
    if year < 1400 or year > 1900:
        return None
    return year


def normalize_events(aanstelling: pd.DataFrame) -> pd.DataFrame:
    """Normalize aanstelling-like rows into career events.

    Accepts either raw ``raa.aanstelling`` columns (``id``, ``van``, …) or
    already-aliased event columns (``aanstelling_id``, …).
    """
    if aanstelling.empty:
        return _empty_events()

    frame = sanitize_aanstelling_years(aanstelling.copy())
    if "aanstelling_id" not in frame.columns and "id" in frame.columns:
        frame = frame.rename(columns={"id": "aanstelling_id"})

    required = ("aanstelling_id", "persoon_id", "functie_id", "instelling_id")
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise ValueError(f"normalize_events missing columns: {missing}")

    for col in ("van", "tot"):
        if col not in frame.columns:
            frame[col] = pd.NA

    van_period = frame["van"].map(_parse_period)
    tot_period = frame["tot"].map(_parse_period)
    # Drop periods whose year is out of bounds (sanitize may have left strings).
    van_year = van_period.map(_period_year)
    tot_year = tot_period.map(_period_year)
    van_period = [
        p if y is not None else None for p, y in zip(van_period, van_year, strict=True)
    ]
    tot_period = [
        p if y is not None else None for p, y in zip(tot_period, tot_year, strict=True)
    ]

    out = pd.DataFrame(
        {
            "aanstelling_id": frame["aanstelling_id"].astype("Int64"),
            "persoon_id": frame["persoon_id"].astype("Int64"),
            "functie_id": frame["functie_id"].astype("Int64"),
            "instelling_id": frame["instelling_id"].astype("Int64"),
            "van": frame["van"],
            "tot": frame["tot"],
            "van_period": van_period,
            "tot_period": tot_period,
            "van_year": pd.Series(van_year, dtype="Int64"),
            "tot_year": pd.Series(tot_year, dtype="Int64"),
            "is_undated": pd.Series(van_year, dtype="Int64").isna(),
        }
    )

    for col in (
        "functie_naam",
        "instelling_naam",
        "persoon_naam",
        "van_als_bekend",
        "tot_als_bekend",
        "vertegenwoordigend",
        "provincie_id",
        *PERIOD_FLAG_COLS,
    ):
        if col in frame.columns:
            out[col] = frame[col].values

    return out.reset_index(drop=True)


def load_events(engine: "Engine") -> pd.DataFrame:
    """Load career events from Postgres ``raa.aanstelling`` with name joins."""
    from sqlalchemy import text

    with engine.connect() as conn:
        raw = pd.read_sql(text(_EVENTS_SQL), conn)
    return normalize_events(raw)


def events_for_export(events: pd.DataFrame) -> pd.DataFrame:
    """Drop non-parquet-friendly Period columns; keep ISO strings and years."""
    drop = [c for c in ("van_period", "tot_period") if c in events.columns]
    return events.drop(columns=drop)


def _empty_events() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "aanstelling_id",
            "persoon_id",
            "functie_id",
            "instelling_id",
            "van",
            "tot",
            "van_period",
            "tot_period",
            "van_year",
            "tot_year",
            "is_undated",
        ]
    )
