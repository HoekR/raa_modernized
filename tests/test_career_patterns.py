from __future__ import annotations

import pandas as pd

from raa_career_patterns import (
    aggregate_matrix,
    build_sequences,
    filter_events,
    normalize_events,
    pairwise_transitions,
)


def _raw_rows(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_ordering_null_van_last():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 10,
                "functie_id": 1,
                "instelling_id": 100,
                "van": pd.NA,
                "tot": pd.NA,
            },
            {
                "id": 2,
                "persoon_id": 10,
                "functie_id": 2,
                "instelling_id": 200,
                "van": "1700-01-01",
                "tot": "1710-01-01",
            },
            {
                "id": 3,
                "persoon_id": 10,
                "functie_id": 3,
                "instelling_id": 300,
                "van": "1690-01-01",
                "tot": "1695-01-01",
            },
        ]
    )
    events = normalize_events(raw)
    seq = build_sequences(events)
    dated = seq.loc[seq["seq_idx"].notna()].sort_values("seq_idx")
    assert dated["aanstelling_id"].tolist() == [3, 2]
    undated = seq.loc[seq["seq_idx"].isna()]
    assert len(undated) == 1
    assert undated.iloc[0]["aanstelling_id"] == 1


def test_overlap_grouping():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 1,
                "instelling_id": 10,
                "van": "1600-01-01",
                "tot": "1610-12-31",
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 2,
                "instelling_id": 20,
                "van": "1605-01-01",
                "tot": "1615-12-31",
            },
            {
                "id": 3,
                "persoon_id": 1,
                "functie_id": 3,
                "instelling_id": 30,
                "van": "1620-01-01",
                "tot": "1630-12-31",
            },
        ]
    )
    seq = build_sequences(normalize_events(raw))
    by_id = seq.set_index("aanstelling_id")
    assert by_id.loc[1, "overlap_group_id"] == by_id.loc[2, "overlap_group_id"]
    assert by_id.loc[3, "overlap_group_id"] != by_id.loc[1, "overlap_group_id"]


def test_transition_skip_on_overlap():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 1,
                "instelling_id": 10,
                "van": "1600-01-01",
                "tot": "1610-12-31",
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 2,
                "instelling_id": 20,
                "van": "1605-01-01",
                "tot": "1615-12-31",
            },
            {
                "id": 3,
                "persoon_id": 1,
                "functie_id": 3,
                "instelling_id": 30,
                "van": "1620-01-01",
                "tot": "1630-12-31",
            },
        ]
    )
    seq = build_sequences(normalize_events(raw))
    edges = pairwise_transitions(seq)
    assert len(edges) == 2
    first = edges.loc[edges["from_aanstelling_id"] == 1].iloc[0]
    assert first["skipped_overlap"] is True or first["skipped_overlap"] == True
    second = edges.loc[edges["from_aanstelling_id"] == 2].iloc[0]
    assert second["skipped_overlap"] is False or second["skipped_overlap"] == False

    matrix = aggregate_matrix(edges, grain="instelling")
    assert len(matrix) == 1
    assert matrix.iloc[0]["from_id"] == 20
    assert matrix.iloc[0]["to_id"] == 30
    assert matrix.iloc[0]["count"] == 1
    assert matrix.iloc[0]["probability"] == 1.0


def test_matrix_functie_and_instelling_grains():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1700-01-01",
                "tot": "1705-01-01",
                "functie_naam": "Burgemeester",
                "instelling_naam": "Amsterdam",
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 20,
                "instelling_id": 200,
                "van": "1710-01-01",
                "tot": "1715-01-01",
                "functie_naam": "Schepen",
                "instelling_naam": "Haarlem",
            },
            {
                "id": 3,
                "persoon_id": 2,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1700-01-01",
                "tot": "1702-01-01",
                "functie_naam": "Burgemeester",
                "instelling_naam": "Amsterdam",
            },
            {
                "id": 4,
                "persoon_id": 2,
                "functie_id": 20,
                "instelling_id": 200,
                "van": "1705-01-01",
                "tot": "1708-01-01",
                "functie_naam": "Schepen",
                "instelling_naam": "Haarlem",
            },
        ]
    )
    edges = pairwise_transitions(build_sequences(normalize_events(raw)))
    inst = aggregate_matrix(edges, grain="instelling")
    assert len(inst) == 1
    assert inst.iloc[0]["count"] == 2
    assert inst.iloc[0]["from_id"] == 100
    assert inst.iloc[0]["to_id"] == 200

    func = aggregate_matrix(edges, grain="functie")
    assert len(func) == 1
    assert func.iloc[0]["from_id"] == 10
    assert func.iloc[0]["to_id"] == 20
    assert func.iloc[0]["count"] == 2

    office = aggregate_matrix(edges, grain="office")
    assert len(office) == 1
    assert office.iloc[0]["from_id"] == "10:100"
    assert office.iloc[0]["to_id"] == "20:200"


def test_same_day_succession_is_not_overlap():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 1,
                "instelling_id": 10,
                "van": "1600-01-01",
                "tot": "1610-01-01",
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 2,
                "instelling_id": 20,
                "van": "1610-01-01",
                "tot": "1620-01-01",
            },
        ]
    )
    edges = pairwise_transitions(build_sequences(normalize_events(raw)))
    assert len(edges) == 1
    assert edges.iloc[0]["skipped_overlap"] is False or edges.iloc[0]["skipped_overlap"] == False
    matrix = aggregate_matrix(edges, grain="instelling")
    assert len(matrix) == 1
    assert matrix.iloc[0]["count"] == 1


def test_consecutive_reappointments_collapse_to_one_job():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1700-01-01",
                "tot": "1703-01-01",
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1703-01-01",
                "tot": "1706-01-01",
            },
            {
                "id": 3,
                "persoon_id": 1,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1706-01-01",
                "tot": "1709-01-01",
            },
        ]
    )
    seq = build_sequences(normalize_events(raw))
    dated = seq.loc[seq["seq_idx"].notna()]
    assert len(dated) == 1
    assert dated.iloc[0]["n_appointments"] == 3
    assert dated.iloc[0]["first_aanstelling_id"] == 1
    assert dated.iloc[0]["last_aanstelling_id"] == 3
    assert str(dated.iloc[0]["tot"]).startswith("1709")
    assert pairwise_transitions(seq).empty


def test_return_after_other_job_is_two_spells():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1700-01-01",
                "tot": "1702-01-01",
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 20,
                "instelling_id": 200,
                "van": "1703-01-01",
                "tot": "1705-01-01",
            },
            {
                "id": 3,
                "persoon_id": 1,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1706-01-01",
                "tot": "1708-01-01",
            },
        ]
    )
    seq = build_sequences(normalize_events(raw))
    dated = seq.loc[seq["seq_idx"].notna()].sort_values("seq_idx")
    assert len(dated) == 3
    assert dated["n_appointments"].tolist() == [1, 1, 1]
    edges = pairwise_transitions(seq)
    assert len(edges) == 2
    assert edges.iloc[0]["from_functie_id"] == 10
    assert edges.iloc[0]["to_functie_id"] == 20
    assert edges.iloc[1]["from_functie_id"] == 20
    assert edges.iloc[1]["to_functie_id"] == 10


def test_require_complete_office_drops_null_fks():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 10,
                "instelling_id": 100,
                "van": "1700-01-01",
                "tot": "1701-01-01",
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 20,
                "instelling_id": pd.NA,
                "van": "1702-01-01",
                "tot": "1703-01-01",
            },
            {
                "id": 3,
                "persoon_id": 1,
                "functie_id": pd.NA,
                "instelling_id": 200,
                "van": "1704-01-01",
                "tot": "1705-01-01",
            },
        ]
    )
    events = normalize_events(raw)
    kept = filter_events(events, require_complete_office=True)
    assert len(kept) == 1
    assert kept.iloc[0]["aanstelling_id"] == 1
    all_rows = filter_events(events, require_complete_office=False)
    assert len(all_rows) == 3


def test_period_filter_reduces_input():
    raw = _raw_rows(
        [
            {
                "id": 1,
                "persoon_id": 1,
                "functie_id": 1,
                "instelling_id": 1,
                "van": "1500-01-01",
                "tot": "1510-01-01",
                "me": 1,
                "republiek": 0,
            },
            {
                "id": 2,
                "persoon_id": 1,
                "functie_id": 2,
                "instelling_id": 2,
                "van": "1650-01-01",
                "tot": "1660-01-01",
                "me": 0,
                "republiek": 1,
            },
        ]
    )
    events = normalize_events(raw)
    filtered = filter_events(events, period_flags=["republiek"])
    assert len(filtered) == 1
    assert filtered.iloc[0]["aanstelling_id"] == 2

    by_year = filter_events(events, year_min=1600, year_max=1700)
    assert len(by_year) == 1
    assert by_year.iloc[0]["aanstelling_id"] == 2

    min_posts = filter_events(events, min_posts=2)
    assert len(min_posts) == 2
    alone = filter_events(events, period_flags=["me"], min_posts=2)
    assert alone.empty
