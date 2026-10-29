from __future__ import annotations

import pandas as pd

from raa_career_patterns.circulation import (
    circulation_by_era,
    dense_node_label,
    filter_dense_circulation,
    in_dense_subgraph,
    top_dense_edges_by_era,
)


def test_dense_subgraph_labels():
    assert in_dense_subgraph("Staten-Generaal der Verenigde Nederlanden (1576-1795)")
    assert dense_node_label("Raad van State (1588-1795)") == "Raad van State"
    assert dense_node_label("Admiraliteit te Amsterdam (1586-1795)") == "Admiraliteit"
    assert not in_dense_subgraph("Hof van Holland")
    assert dense_node_label("Hof van Holland") == "other"


def test_circulation_by_era_brackets_1672():
    transitions = pd.DataFrame(
        [
            {
                "persoon_id": 1,
                "from_instelling_naam": "Staten-Generaal (1576-1795)",
                "to_instelling_naam": "Raad van State (1588-1795)",
                "from_instelling_id": 1,
                "to_instelling_id": 2,
                "to_van": "1660-01-01",
                "skipped_overlap": False,
            },
            {
                "persoon_id": 2,
                "from_instelling_naam": "Raad van State (1588-1795)",
                "to_instelling_naam": "Staten-Generaal (1576-1795)",
                "from_instelling_id": 2,
                "to_instelling_id": 1,
                "to_van": "1680-01-01",
                "skipped_overlap": False,
            },
            {
                "persoon_id": 3,
                "from_instelling_naam": "Hof van Holland",
                "to_instelling_naam": "Rekenkamer",
                "from_instelling_id": 9,
                "to_instelling_id": 10,
                "to_van": "1680-01-01",
                "skipped_overlap": False,
            },
        ]
    )
    dense = filter_dense_circulation(transitions)
    assert len(dense) == 2
    by_era = circulation_by_era(transitions)
    pre = by_era.loc[by_era["era"] == "1651–1671"].iloc[0]
    post = by_era.loc[by_era["era"] == "1672–1712"].iloc[0]
    assert pre["n_dense_hops"] == 1
    assert post["n_dense_hops"] == 1
    edges = top_dense_edges_by_era(transitions, n=3)
    assert set(edges["era"]) >= {"1651–1671", "1672–1712"}
