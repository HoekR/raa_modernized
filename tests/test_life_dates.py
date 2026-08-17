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


def test_parse_edtf_open_after_point():
    assert parse_edtf_interval(">1770") == YearInterval(1770, None)


def test_shadow_death_uses_last_tot_for_search_and_open_edtf_for_display():
    persoon = pd.DataFrame(
        [
            {
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
        ]
    )
    aanst = pd.DataFrame(
        [
            {"persoon_id": 1, "van": "1800-01-01", "tot": "1770-12-31"},
            {"persoon_id": 1, "van": "1750-01-01", "tot": "1765-12-31"},
        ]
    )
    row = enrich_persoon_life_dates(persoon, aanst).iloc[0]
    assert row["life_end_source"] == "shadow"
    assert row["life_end_year"] == 1770
    assert row["life_end_edtf"] == ">1770"


def test_shadow_death_skipped_without_tot():
    persoon = pd.DataFrame(
        [
            {
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
        ]
    )
    aanst = pd.DataFrame([{"persoon_id": 1, "van": "1750-01-01", "tot": None}])
    row = enrich_persoon_life_dates(persoon, aanst).iloc[0]
    assert row["life_end_source"] is None
    assert pd.isna(row["life_end_year"])
    assert row["life_end_edtf"] is None or pd.isna(row["life_end_edtf"])


def test_shadow_death_after_last_appointment():
    persoon = pd.DataFrame(
        [
            {
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
        ]
    )
    aanst = pd.DataFrame(
        [{"persoon_id": 1, "van": "1750-01-01", "tot": "1770-12-31"}]
    )
    row = enrich_persoon_life_dates(persoon, aanst).iloc[0]
    assert row["life_end_source"] == "shadow"
    assert row["life_end_year"] == 1770
    assert row["life_end_edtf"] == ">1770"


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
