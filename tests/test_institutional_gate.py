from __future__ import annotations

import pandas as pd

from raa_life_dates.institutional_gate import apply_institutional_date_gate, appointment_van_year


def test_appointment_van_year_parses_iso():
    assert appointment_van_year("1750-06-01") == 1750
    assert appointment_van_year("1750") == 1750
    assert appointment_van_year("") is None
    assert appointment_van_year(None) is None


def test_institutional_gate_drops_undated_and_orphan_personen():
    extab = {
        "persoon": pd.DataFrame({"id": [1, 2, 3]}),
        "aanstelling": pd.DataFrame(
            {
                "persoon_id": [1, 1, 2, 3],
                "van": ["1750-01-01", None, "", "1800-01-01"],
                "tot": ["1770-12-31", "1770-12-31", "1810-01-01", None],
            }
        ),
        "alias": pd.DataFrame({"persoon_id": [2, 3], "naam": ["a", "b"]}),
    }
    cleaned, stats = apply_institutional_date_gate(extab)
    assert stats["aanstelling_undated"] == 2
    assert stats["persoon_no_dated_aanstelling"] == 1
    assert set(cleaned["persoon"]["id"]) == {1, 3}
    assert len(cleaned["aanstelling"]) == 2
    assert len(cleaned["alias"]) == 1
    assert set(cleaned["alias"]["persoon_id"]) == {3}
