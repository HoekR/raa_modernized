import pytest

from raa_api.edtf_bounds import life_year_overlap_sql


def test_life_year_overlap_sql_with_shadow():
    sql, params = life_year_overlap_sql("geboorte", "1720/1750", include_shadow=True, param_prefix="g0")
    assert "COALESCE(p.geboorte_year, p.life_start_year)" in sql
    assert params == {"g0_start": 1720, "g0_end": 1750}


def test_life_year_overlap_sql_exact_only():
    sql, params = life_year_overlap_sql("overlijden", "../1800", include_shadow=False, param_prefix="o0")
    assert sql.startswith("p.overlijden_year IS NOT NULL")
    assert "life_end_year" not in sql
    assert params == {"o0_end": 1800}


def test_life_year_overlap_sql_rejects_invalid():
    with pytest.raises(ValueError):
        life_year_overlap_sql("geboorte", "not-a-date", include_shadow=True, param_prefix="x")
