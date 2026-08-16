from __future__ import annotations

import pandas as pd

from raa_entity_spans.spans import build_functie_attestation, build_functie_instelling_span


def test_functie_instelling_span_witnesses():
    aanstelling = pd.DataFrame(
        [
            {
                "id": 10,
                "functie_id": 1,
                "instelling_id": 100,
                "van": "1600-01-01",
                "tot": "1650-12-31",
                "van_als_bekend": "1600",
                "tot_als_bekend": "1650",
            },
            {
                "id": 11,
                "functie_id": 1,
                "instelling_id": 100,
                "van": "1600-01-01",
                "tot": "1700-01-01",
                "van_als_bekend": "1600",
                "tot_als_bekend": "1700",
            },
            {
                "id": 20,
                "functie_id": 1,
                "instelling_id": 200,
                "van": "1795-01-01",
                "tot": "1811-01-01",
                "van_als_bekend": "1795",
                "tot_als_bekend": "1811",
            },
        ]
    )
    instelling = pd.DataFrame(
        [
            {"id": 100, "naam": "Staten van Friesland"},
            {"id": 200, "naam": "Departement Friesland"},
        ]
    )
    span = build_functie_instelling_span(aanstelling, instelling)
    assert len(span) == 2
    fries = span.loc[span["instelling_id"] == 100].iloc[0]
    assert fries["first_year"] == 1600
    assert fries["last_year"] == 1700
    assert fries["first_aanstelling_id"] == 10
    assert fries["last_aanstelling_id"] == 11
    assert fries["span_label"] == "1600 – 1700"

    attestation = build_functie_attestation(span, aanstelling, instelling)
    row = attestation.iloc[0]
    assert row["corpus_first_year"] == 1600
    assert row["corpus_last_year"] == 1811
    assert row["corpus_first_instelling_id"] == 100
    assert row["corpus_last_instelling_id"] == 200
    assert row["instelling_count"] == 2


def test_functie_instelling_span_ignores_undated_for_extremes():
    aanstelling = pd.DataFrame(
        [
            {
                "id": 1,
                "functie_id": 2,
                "instelling_id": 3,
                "van": pd.NA,
                "tot": pd.NA,
                "van_als_bekend": "",
                "tot_als_bekend": "",
            },
            {
                "id": 2,
                "functie_id": 2,
                "instelling_id": 3,
                "van": "1701-05-01",
                "tot": "1710-01-01",
                "van_als_bekend": "1701",
                "tot_als_bekend": "1710",
            },
        ]
    )
    instelling = pd.DataFrame([{"id": 3, "naam": "Test instelling"}])
    span = build_functie_instelling_span(aanstelling, instelling)
    assert len(span) == 1
    assert span.iloc[0]["first_year"] == 1701
    assert span.iloc[0]["last_year"] == 1710
    assert span.iloc[0]["aanstelling_count"] == 2
