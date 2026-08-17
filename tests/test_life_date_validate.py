from __future__ import annotations

import pandas as pd

from raa_life_dates.edtf import derive_life_edtf
from raa_life_dates.validate import (
    audit_implausible_recorded_dates,
    is_plausible_life_year,
    raw_recorded_geboorte_year,
    sanitize_implausible_recorded_dates,
)


def _person_row(**overrides) -> pd.Series:
    base = {
        "id": 1,
        "geboortedatum": pd.NA,
        "geboortejaar": pd.NA,
        "geboortemaand": pd.NA,
        "geboortedag": pd.NA,
        "onbepaaldgeboortedatum": 0,
        "geboortedatum_als_bekend": "",
        "overlijdensdatum": pd.NA,
        "overlijdensjaar": pd.NA,
        "overlijdensmaand": pd.NA,
        "overlijdensdag": pd.NA,
        "onbepaaldoverlijdensdatum": 0,
        "overlijdensdatum_als_bekend": "",
    }
    base.update(overrides)
    return pd.Series(base)


def test_implausible_geboortejaar_rejected_by_derive():
    row = _person_row(geboortejaar=10, geboortedatum_als_bekend="10")
    geb, ovl, gy, oy = derive_life_edtf(row)
    assert geb is None
    assert gy is None
    assert raw_recorded_geboorte_year(row) == 10


def test_sanitize_clears_implausible_geboorte_fields():
    persoon = pd.DataFrame([_person_row(geboortejaar=10, geboortedatum_als_bekend="10").to_dict()])
    cleaned, stats = sanitize_implausible_recorded_dates(persoon)
    assert stats["geboorte_cleared"] == 1
    row = cleaned.iloc[0]
    assert pd.isna(row["geboortejaar"])
    assert pd.isna(row["geboortedatum_als_bekend"])
    _, _, gy, _ = derive_life_edtf(row)
    assert gy is None


def test_audit_lists_implausible_rows():
    persoon = pd.DataFrame(
        [
            _person_row(id=7, geboortejaar=10, geboortedatum_als_bekend="10").to_dict(),
            _person_row(id=8, geboortejaar=1750, geboortedatum_als_bekend="1750").to_dict(),
        ]
    )
    flagged = audit_implausible_recorded_dates(persoon)
    assert len(flagged) == 1
    assert flagged[0]["id"] == 7
    assert "geboorte=10" in flagged[0]["issues"]


def test_plausible_bounds():
    assert not is_plausible_life_year(10)
    assert is_plausible_life_year(1750)
    assert not is_plausible_life_year(2100)
