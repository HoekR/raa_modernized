from __future__ import annotations

import pandas as pd

from raa_career_patterns.discontinuity import (
    compare_windows,
    influence_layer,
    layer_move,
    summarize_window,
)
from raa_career_patterns.events import normalize_events


def test_influence_layer_ranking():
    assert influence_layer("Staten-Generaal", 0) == "generaliteit"
    assert influence_layer("Raad van State", 0) == "generaliteit"
    assert influence_layer("Staten van Holland", 1) == "supra"
    assert influence_layer("Schepenbank X", 0) == "local"
    assert layer_move("local", "supra") == "rose"
    assert layer_move("generaliteit", "local") == "fell"
    assert layer_move("supra", "supra") == "same"


def test_cut_window_more_instelling_hops_than_quiet():
    """Synthetic: quiet keeps same office; cut forces new instelling_id."""
    rows = [
        # Quiet crosser 1760 — same institution
        {
            "id": 1,
            "persoon_id": 10,
            "functie_id": 1,
            "instelling_id": 100,
            "van": "1755-01-01",
            "tot": "1759-01-01",
            "instelling_naam": "College A",
            "vertegenwoordigend": 0,
        },
        {
            "id": 2,
            "persoon_id": 10,
            "functie_id": 1,
            "instelling_id": 100,
            "van": "1761-01-01",
            "tot": "1765-01-01",
            "instelling_naam": "College A",
            "vertegenwoordigend": 0,
        },
        # Cut crosser 1795 — re-keyed institution (political/editorial hop)
        {
            "id": 3,
            "persoon_id": 20,
            "functie_id": 2,
            "instelling_id": 200,
            "van": "1790-01-01",
            "tot": "1794-01-01",
            "instelling_naam": "Staten-Generaal",
            "vertegenwoordigend": 0,
        },
        {
            "id": 4,
            "persoon_id": 20,
            "functie_id": 2,
            "instelling_id": 201,
            "van": "1796-01-01",
            "tot": "1800-01-01",
            "instelling_naam": "Nationale Vergadering",
            "vertegenwoordigend": 1,
        },
    ]
    events = normalize_events(pd.DataFrame(rows))
    summary, crossings = compare_windows(events, ["quiet_1760", "cut_1795"])

    quiet = summary.loc[
        (summary["window_label"] == "quiet_1760") & (summary["stratum"] == "all")
    ].iloc[0]
    cut = summary.loc[
        (summary["window_label"] == "cut_1795") & (summary["stratum"] == "all")
    ].iloc[0]
    assert quiet["n_crossers"] == 1
    assert cut["n_crossers"] == 1
    assert quiet["same_instelling_rate"] == 1.0
    assert cut["same_instelling_rate"] == 0.0

    cut_row = crossings.loc[crossings["window_label"] == "cut_1795"].iloc[0]
    assert cut_row["stratum"] == "generaliteit"
    assert cut_row["pre_layer"] == "generaliteit"
    assert cut_row["post_layer"] == "supra"
    assert cut_row["layer_move"] == "fell"


def test_summarize_empty_window():
    events = normalize_events(
        pd.DataFrame(
            [
                {
                    "id": 1,
                    "persoon_id": 1,
                    "functie_id": 1,
                    "instelling_id": 1,
                    "van": "1500-01-01",
                    "tot": "1501-01-01",
                }
            ]
        )
    )
    summary = summarize_window(events, cut_year=1795, window_label="cut_1795")
    assert summary.loc[summary["stratum"] == "all", "n_crossers"].iloc[0] == 0
