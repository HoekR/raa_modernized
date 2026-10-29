"""Filters for career event frames."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from raa_career_patterns.events import PERIOD_FLAG_COLS


def filter_events(
    events: pd.DataFrame,
    *,
    period_flags: Iterable[str] | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    drop_undated: bool = False,
    require_complete_office: bool = True,
    min_posts: int | None = None,
) -> pd.DataFrame:
    """Filter career events before sequence/transition building.

    ``period_flags`` — keep rows where any listed flag column is truthy
    (e.g. ``("republiek", "batfra")``).

    ``year_min`` / ``year_max`` — keep dated rows whose ``van_year`` falls in
    ``[year_min, year_max]`` (inclusive). Undated rows are dropped when either
    bound is set.

    ``require_complete_office`` — drop rows missing ``functie_id`` or
    ``instelling_id`` (default True). Those gaps are mostly content/modelling
    issues; for politics/influence analysis they pollute transitions as a
    fake “unknown office”.

    ``min_posts`` — after other filters, keep only persons with at least this
    many remaining rows (including undated unless ``drop_undated``).
    """
    if events.empty:
        return events.copy()

    out = events
    if require_complete_office:
        mask = out["functie_id"].notna() & out["instelling_id"].notna()
        out = out.loc[mask]

    if period_flags:
        flags = list(period_flags)
        unknown = [f for f in flags if f not in PERIOD_FLAG_COLS]
        if unknown:
            raise ValueError(
                f"Unknown period flags {unknown}; expected one of {PERIOD_FLAG_COLS}"
            )
        present = [f for f in flags if f in out.columns]
        if not present:
            return out.iloc[0:0].copy()
        mask = False
        for col in present:
            mask = mask | (out[col].fillna(0).astype(int) != 0)
        out = out.loc[mask]

    if year_min is not None or year_max is not None:
        years = out["van_year"]
        mask = years.notna()
        if year_min is not None:
            mask = mask & (years >= year_min)
        if year_max is not None:
            mask = mask & (years <= year_max)
        out = out.loc[mask]

    if drop_undated:
        out = out.loc[~out["is_undated"]]

    if min_posts is not None and min_posts > 0 and not out.empty:
        counts = out.groupby("persoon_id", sort=False).size()
        keep = counts[counts >= min_posts].index
        out = out.loc[out["persoon_id"].isin(keep)]

    return out.reset_index(drop=True)
