from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
import pytest

from raa_life_dates.edtf import YearInterval, derive_life_edtf, parse_edtf_interval
from raa_life_dates.shadow import enrich_persoon_life_dates


def test_parse_edtf_closed_interval():
    assert parse_edtf_interval("1720/1750") == YearInterval(1720, 1750)


def test_parse_edtf_open_ends():
    assert parse_edtf_interval("../1720") == YearInterval(None, 1720)
    assert parse_edtf_interval("1720/..") == YearInterval(1720, None)


def test_parse_edtf_point_with_qualifier():
    assert parse_edtf_interval("1720~") == YearInterval(1720, 1720)


def test_year_interval_overlap():
    assert YearInterval(1700, 1750).overlaps(YearInterval(1740, 1780))
    assert not YearInterval(1700, 1730).overlaps(YearInterval(1740, 1780))


def test_derive_life_edtf_year_only_with_approx():
    row = pd.Series(
        {
            "geboortedatum": pd.NA,
            "geboortejaar": 1767,
            "geboortemaand": pd.NA,
            "geboortedag": pd.NA,
            "onbepaaldgeboortedatum": 1,
            "geboortedatum_als_bekend": "1767",
            "overlijdensdatum": pd.NA,
            "overlijdensjaar": pd.NA,
            "overlijdensmaand": pd.NA,
            "overlijdensdag": pd.NA,
            "onbepaaldoverlijdensdatum": 0,
            "overlijdensdatum_als_bekend": "",
        }
    )
    geb, ovl, gy, oy = derive_life_edtf(row)
    assert geb == "1767~"
    assert gy == 1767
    assert ovl is None
    assert oy is None


@pytest.mark.skipif(
    not Path.home().joinpath("develop/raa_convert/extab.pkl").exists(),
    reason="extab.pkl not available",
)
def test_enrich_persoon_life_dates_smoke():
    with Path.home().joinpath("develop/raa_convert/extab.pkl").open("rb") as handle:
        extab = pickle.load(handle)
    enriched = enrich_persoon_life_dates(extab["persoon"].head(200), extab["aanstelling"])
    assert "life_start_year" in enriched.columns
    assert enriched["life_start_year"].notna().any()
