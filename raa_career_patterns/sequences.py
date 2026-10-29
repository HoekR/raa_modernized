"""Per-person ordered career sequences and overlap groups."""

from __future__ import annotations

from typing import Any

import pandas as pd


def _period_lt(a: Any, b: Any) -> bool:
    """True if period a < b; missing b (open end) is treated as +infinity."""
    if b is None:
        return True
    if a is None:
        return True
    return a < b


def intervals_overlap(
    van_a: Any,
    tot_a: Any,
    van_b: Any,
    tot_b: Any,
) -> bool:
    """Interval overlap; missing tot = open-ended.

    Endpoint-touching spans (A.tot == B.van) are **not** overlaps, so same-day
    succession still yields a transition edge.
    """
    if van_a is None or van_b is None:
        return False
    return _period_lt(van_a, tot_b) and _period_lt(van_b, tot_a)


def _overlap_group_ids(dated: pd.DataFrame) -> list[int | None]:
    """Connected components of overlapping intervals within one person."""
    n = len(dated)
    if n == 0:
        return []
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    vans = dated["van_period"].tolist()
    tots = dated["tot_period"].tolist()
    for i in range(n):
        for j in range(i + 1, n):
            if intervals_overlap(vans[i], tots[i], vans[j], tots[j]):
                union(i, j)

    root_to_gid: dict[int, int] = {}
    next_gid = 0
    result: list[int | None] = []
    for i in range(n):
        root = find(i)
        # Singleton non-overlapping posts still get a group id for traceability.
        if root not in root_to_gid:
            root_to_gid[root] = next_gid
            next_gid += 1
        result.append(root_to_gid[root])
    return result


def _same_office(a: dict, b: dict) -> bool:
    return a["functie_id"] == b["functie_id"] and a["instelling_id"] == b["instelling_id"]


def _period_is_missing(period: Any) -> bool:
    if period is None or (isinstance(period, float) and pd.isna(period)):
        return True
    try:
        return bool(pd.isna(period))
    except (TypeError, ValueError):
        return False


def _latest_tot(rows: list[dict]) -> tuple[Any, Any, Any]:
    """Pick the latest non-null tot among rows; else (None, None, None)."""
    best_period = None
    best_tot = None
    best_year = None
    for row in rows:
        period = row.get("tot_period")
        if _period_is_missing(period):
            continue
        if best_period is None or period > best_period:
            best_period = period
            best_tot = row.get("tot")
            best_year = row.get("tot_year")
    return best_tot, best_period, best_year


def collapse_consecutive_offices(dated: pd.DataFrame) -> pd.DataFrame:
    """Merge consecutive same-office rows into one job spell.

    Same office = same ``functie_id`` + ``instelling_id``. A return to the same
    office after a different job is a **new** spell (not merged).
    """
    if dated.empty:
        return dated

    records = dated.to_dict("records")
    spells: list[dict] = []
    run: list[dict] = [records[0]]

    def flush(run_rows: list[dict]) -> None:
        first = run_rows[0]
        last = run_rows[-1]
        tot, tot_period, tot_year = _latest_tot(run_rows)
        spell = dict(first)
        spell["tot"] = tot
        spell["tot_period"] = tot_period
        spell["tot_year"] = tot_year
        spell["aanstelling_id"] = first["aanstelling_id"]
        spell["first_aanstelling_id"] = first["aanstelling_id"]
        spell["last_aanstelling_id"] = last["aanstelling_id"]
        spell["n_appointments"] = len(run_rows)
        spells.append(spell)

    for row in records[1:]:
        if _same_office(run[-1], row):
            run.append(row)
        else:
            flush(run)
            run = [row]
    flush(run)

    return pd.DataFrame(spells)


def build_sequences(
    events: pd.DataFrame,
    *,
    collapse_reappointments: bool = True,
) -> pd.DataFrame:
    """Build a long-table career sequence from normalized events.

    Dated posts (``is_undated`` false) receive ``seq_idx`` 0..n-1 per person,
    ordered by ``van_period`` ascending then ``aanstelling_id``. Undated posts
    keep ``seq_idx`` null and ``overlap_group_id`` null.

    When ``collapse_reappointments`` is true (default), consecutive appointments
    to the same office (functie × instelling) become one job spell so pairwise
    transitions skip trivial reappointments. Returning to the same office after
    another job counts as a second spell.
    """
    if events.empty:
        return _empty_sequences()

    parts: list[pd.DataFrame] = []
    for _persoon_id, group in events.groupby("persoon_id", sort=False):
        dated = group.loc[~group["is_undated"]].copy()
        undated = group.loc[group["is_undated"]].copy()
        frames: list[pd.DataFrame] = []

        if not dated.empty:
            dated = dated.sort_values(
                by=["van_period", "aanstelling_id"],
                ascending=[True, True],
                kind="mergesort",
            ).reset_index(drop=True)
            if collapse_reappointments:
                dated = collapse_consecutive_offices(dated)
            else:
                dated = dated.copy()
                dated["first_aanstelling_id"] = dated["aanstelling_id"]
                dated["last_aanstelling_id"] = dated["aanstelling_id"]
                dated["n_appointments"] = 1
            dated = dated.reset_index(drop=True)
            dated["seq_idx"] = range(len(dated))
            dated["overlap_group_id"] = _overlap_group_ids(dated)
            frames.append(dated)

        if not undated.empty:
            undated = undated.sort_values(
                by=["aanstelling_id"], kind="mergesort"
            ).reset_index(drop=True)
            undated["seq_idx"] = pd.NA
            undated["overlap_group_id"] = pd.NA
            undated["first_aanstelling_id"] = undated["aanstelling_id"]
            undated["last_aanstelling_id"] = undated["aanstelling_id"]
            undated["n_appointments"] = 1
            frames.append(undated)

        if frames:
            parts.append(pd.concat(frames, ignore_index=True))

    if not parts:
        return _empty_sequences()
    result = pd.concat(parts, ignore_index=True)
    result["seq_idx"] = result["seq_idx"].astype("Int64")
    result["overlap_group_id"] = result["overlap_group_id"].astype("Int64")
    result["persoon_id"] = result["persoon_id"].astype("Int64")
    result["n_appointments"] = result["n_appointments"].astype("Int64")
    return result


def sequences_for_export(sequences: pd.DataFrame) -> pd.DataFrame:
    drop = [c for c in ("van_period", "tot_period") if c in sequences.columns]
    return sequences.drop(columns=drop)


def _empty_sequences() -> pd.DataFrame:
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
            "seq_idx",
            "overlap_group_id",
            "first_aanstelling_id",
            "last_aanstelling_id",
            "n_appointments",
        ]
    )
