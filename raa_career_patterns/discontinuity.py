"""F-RQ0: politics & influence — career breaks around wetsverzetting cuts."""

from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

# Heuristic Generaliteit / federal layer (v0 — refine with historian list later).
_GENERALITEIT_RE = re.compile(
    r"(staten[\s\-]*generaal|raad\s+van\s+sta|generaliteit)",
    re.IGNORECASE,
)

LAYER_RANK = {"local": 0, "supra": 1, "generaliteit": 2}

# Named windows: synthetic "cut" year + half-width (years on each side).
# Political breakpoints (historian-chosen) vs quiet controls that do not
# overlap those ±10y windows.
DEFAULT_WINDOWS: dict[str, dict[str, int]] = {
    # Political / constitutional stress points
    "cut_1618": {"cut_year": 1618, "half_width": 10},  # Maurits / Synod crisis
    "cut_1651": {"cut_year": 1651, "half_width": 10},  # Grote Vergadering
    "cut_1672": {"cut_year": 1672, "half_width": 10},  # Rampjaar
    "cut_1713": {"cut_year": 1713, "half_width": 10},  # Vrede van Utrecht
    "cut_1795": {"cut_year": 1795, "half_width": 10},  # Bataafse omwenteling
    "cut_1813": {"cut_year": 1813, "half_width": 10},  # einde Franse tijd
    # Quiet controls (away from the cuts above; not overlapping ±10y)
    "quiet_1690": {"cut_year": 1690, "half_width": 10},  # between 1672 and 1713
    "quiet_1760": {"cut_year": 1760, "half_width": 10},  # between 1713 and 1795
}


def is_generaliteit_naam(naam: object) -> bool:
    if naam is None or (isinstance(naam, float) and pd.isna(naam)):
        return False
    text = str(naam).strip()
    if not text:
        return False
    return bool(_GENERALITEIT_RE.search(text))


def influence_layer(instelling_naam: object, vertegenwoordigend: object) -> str:
    """v0 proxy: generaliteit > supra (vertegenwoordigend) > local."""
    if is_generaliteit_naam(instelling_naam):
        return "generaliteit"
    try:
        if vertegenwoordigend is not None and not pd.isna(vertegenwoordigend):
            if int(vertegenwoordigend) != 0:
                return "supra"
    except (TypeError, ValueError):
        pass
    return "local"


def layer_move(pre_layer: str, post_layer: str) -> str:
    pre_r = LAYER_RANK.get(pre_layer, 0)
    post_r = LAYER_RANK.get(post_layer, 0)
    if post_r > pre_r:
        return "rose"
    if post_r < pre_r:
        return "fell"
    return "same"


def _window_bounds(cut_year: int, half_width: int) -> tuple[int, int]:
    return cut_year - half_width, cut_year + half_width


def classify_crossings(
    events: pd.DataFrame,
    *,
    cut_year: int,
    half_width: int = 10,
    window_label: str = "",
) -> pd.DataFrame:
    """One row per person who crosses ``cut_year`` inside the year window.

    Pre/post assignment uses ``van_year`` only (dated posts). Last pre-cut =
    max ``van_year`` among pre; first post-cut = min ``van_year`` among post.
    """
    if events.empty or "van_year" not in events.columns:
        return _empty_crossings()

    year_min, year_max = _window_bounds(cut_year, half_width)
    dated = events.loc[
        events["van_year"].notna()
        & (events["van_year"] >= year_min)
        & (events["van_year"] < year_max)
    ].copy()
    if dated.empty:
        return _empty_crossings()

    dated["van_year"] = dated["van_year"].astype(int)
    if "vertegenwoordigend" not in dated.columns:
        dated["vertegenwoordigend"] = 0

    rows: list[dict] = []

    for persoon_id, group in dated.groupby("persoon_id", sort=False):
        pre = group.loc[group["van_year"] < cut_year]
        post = group.loc[group["van_year"] >= cut_year]
        if pre.empty or post.empty:
            continue

        last_pre = pre.sort_values(
            by=["van_year", "aanstelling_id"], ascending=[False, False], kind="mergesort"
        ).iloc[0]
        first_post = post.sort_values(
            by=["van_year", "aanstelling_id"], ascending=[True, True], kind="mergesort"
        ).iloc[0]

        pre_layer = influence_layer(
            last_pre.get("instelling_naam"), last_pre.get("vertegenwoordigend")
        )
        post_layer = influence_layer(
            first_post.get("instelling_naam"), first_post.get("vertegenwoordigend")
        )
        stratum = (
            "generaliteit"
            if pre_layer == "generaliteit" or post_layer == "generaliteit"
            else "other"
        )

        same_inst = last_pre["instelling_id"] == first_post["instelling_id"]
        same_fun = last_pre["functie_id"] == first_post["functie_id"]
        rows.append(
            {
                "window_label": window_label,
                "cut_year": cut_year,
                "year_min": year_min,
                "year_max": year_max,
                "persoon_id": persoon_id,
                "stratum": stratum,
                "pre_aanstelling_id": last_pre["aanstelling_id"],
                "post_aanstelling_id": first_post["aanstelling_id"],
                "pre_van_year": int(last_pre["van_year"]),
                "post_van_year": int(first_post["van_year"]),
                "pre_functie_id": last_pre["functie_id"],
                "post_functie_id": first_post["functie_id"],
                "pre_instelling_id": last_pre["instelling_id"],
                "post_instelling_id": first_post["instelling_id"],
                "pre_functie_naam": last_pre.get("functie_naam"),
                "post_functie_naam": first_post.get("functie_naam"),
                "pre_instelling_naam": last_pre.get("instelling_naam"),
                "post_instelling_naam": first_post.get("instelling_naam"),
                "pre_layer": pre_layer,
                "post_layer": post_layer,
                "layer_move": layer_move(pre_layer, post_layer),
                "same_instelling": bool(same_inst),
                "same_functie": bool(same_fun),
                "same_office": bool(same_inst and same_fun),
                "gap_years": int(first_post["van_year"]) - int(last_pre["van_year"]),
            }
        )

    if not rows:
        return _empty_crossings()
    return pd.DataFrame(rows)


def summarize_window(
    events: pd.DataFrame,
    *,
    cut_year: int,
    half_width: int = 10,
    window_label: str = "",
) -> pd.DataFrame:
    """Summary metrics for one window, overall + by stratum."""
    year_min, year_max = _window_bounds(cut_year, half_width)
    dated = events.loc[
        events["van_year"].notna()
        & (events["van_year"] >= year_min)
        & (events["van_year"] < year_max)
    ]
    n_persons = int(dated["persoon_id"].nunique()) if not dated.empty else 0
    crossings = classify_crossings(
        events, cut_year=cut_year, half_width=half_width, window_label=window_label
    )

    def _block(frame: pd.DataFrame, stratum: str, persons_denom: int) -> dict:
        n_cross = len(frame)
        if n_cross == 0:
            return {
                "window_label": window_label,
                "cut_year": cut_year,
                "year_min": year_min,
                "year_max": year_max,
                "stratum": stratum,
                "n_persons_in_window": persons_denom,
                "n_crossers": 0,
                "crosser_rate": 0.0 if persons_denom else float("nan"),
                "same_instelling_rate": float("nan"),
                "same_functie_rate": float("nan"),
                "same_office_rate": float("nan"),
                "layer_rose_rate": float("nan"),
                "layer_fell_rate": float("nan"),
                "layer_same_rate": float("nan"),
                "median_gap_years": float("nan"),
            }
        moves = frame["layer_move"]
        return {
            "window_label": window_label,
            "cut_year": cut_year,
            "year_min": year_min,
            "year_max": year_max,
            "stratum": stratum,
            "n_persons_in_window": persons_denom,
            "n_crossers": n_cross,
            "crosser_rate": n_cross / persons_denom if persons_denom else float("nan"),
            "same_instelling_rate": float(frame["same_instelling"].mean()),
            "same_functie_rate": float(frame["same_functie"].mean()),
            "same_office_rate": float(frame["same_office"].mean()),
            "layer_rose_rate": float((moves == "rose").mean()),
            "layer_fell_rate": float((moves == "fell").mean()),
            "layer_same_rate": float((moves == "same").mean()),
            "median_gap_years": float(frame["gap_years"].median()),
        }

    blocks = [_block(crossings, "all", n_persons)]
    for stratum in ("generaliteit", "other"):
        sub = crossings.loc[crossings["stratum"] == stratum]
        blocks.append(_block(sub, stratum, n_persons))

    return pd.DataFrame(blocks)


def compare_windows(
    events: pd.DataFrame,
    window_names: Iterable[str] | None = None,
    *,
    catalog: dict[str, dict[str, int]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run F-RQ0 over named windows.

    Returns ``(summary, crossings)``.
    """
    catalog = catalog or DEFAULT_WINDOWS
    names = list(window_names) if window_names is not None else list(catalog.keys())
    summaries: list[pd.DataFrame] = []
    crossings_parts: list[pd.DataFrame] = []
    for name in names:
        if name not in catalog:
            raise ValueError(f"Unknown window {name!r}; known: {sorted(catalog)}")
        spec = catalog[name]
        cut_year = int(spec["cut_year"])
        half_width = int(spec.get("half_width", 10))
        summaries.append(
            summarize_window(
                events,
                cut_year=cut_year,
                half_width=half_width,
                window_label=name,
            )
        )
        crossings_parts.append(
            classify_crossings(
                events,
                cut_year=cut_year,
                half_width=half_width,
                window_label=name,
            )
        )
    summary = (
        pd.concat(summaries, ignore_index=True) if summaries else _empty_summary()
    )
    crossings = (
        pd.concat(crossings_parts, ignore_index=True)
        if crossings_parts
        else _empty_crossings()
    )
    return summary, crossings


def _empty_crossings() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "window_label",
            "cut_year",
            "year_min",
            "year_max",
            "persoon_id",
            "stratum",
            "pre_aanstelling_id",
            "post_aanstelling_id",
            "pre_van_year",
            "post_van_year",
            "pre_functie_id",
            "post_functie_id",
            "pre_instelling_id",
            "post_instelling_id",
            "pre_functie_naam",
            "post_functie_naam",
            "pre_instelling_naam",
            "post_instelling_naam",
            "pre_layer",
            "post_layer",
            "layer_move",
            "same_instelling",
            "same_functie",
            "same_office",
            "gap_years",
        ]
    )


def _empty_summary() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "window_label",
            "cut_year",
            "year_min",
            "year_max",
            "stratum",
            "n_persons_in_window",
            "n_crossers",
            "crosser_rate",
            "same_instelling_rate",
            "same_functie_rate",
            "same_office_rate",
            "layer_rose_rate",
            "layer_fell_rate",
            "layer_same_rate",
            "median_gap_years",
        ]
    )
