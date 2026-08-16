from raa_api.search import (
    _adel_aanstelling_clause,
    _adel_person_clause,
    _normalize_filter_date,
    _persoon_aanstelling_date_clauses,
    _persoon_text_token_clause,
    _stand_aanstelling_clause,
    _stand_exists_clauses,
)
from raa_api.schemas import SearchRequest


def test_adel_person_clause_enabled():
    assert _adel_person_clause({"adel": ["1"]}) == ["p.adel = 1"]


def test_adel_person_clause_disabled():
    assert _adel_person_clause({}) == []
    assert _adel_person_clause({"adel": ["0"]}) == []


def test_stand_exists_clauses():
    clauses = _stand_exists_clauses("p", {"stand_id": ["3", "7"]})
    assert len(clauses) == 1
    assert "a.stand_id IN (3,7)" in clauses[0]


def test_stand_aanstelling_clause():
    assert _stand_aanstelling_clause({"stand_id": ["2"]}) == ["a.stand_id IN (2)"]


def test_adel_aanstelling_clause():
    assert _adel_aanstelling_clause({"adel": ["true"]}) == ["p.adel = 1"]


def test_persoon_text_token_clause_covers_legacy_identity_fields():
    clause = _persoon_text_token_clause("q0")
    assert "COALESCE(p.search_display, '') ILIKE :q0" in clause
    assert "p.searchable ILIKE :q0" in clause
    assert "raa.alias" in clause


def test_normalize_filter_date_year_only():
    assert _normalize_filter_date("1750") == "1750-01-01"
    assert _normalize_filter_date("1770", end=True) == "1770-12-31"
    assert _normalize_filter_date("1750-06-01") == "1750-06-01"


def test_persoon_aanstelling_date_clauses_overlap():
    req = SearchRequest(filters={"van": ["1750"], "tot": ["1770"]}, period="republiek")
    clauses, params = _persoon_aanstelling_date_clauses(req)
    assert len(clauses) == 1
    assert "EXISTS" in clauses[0]
    assert params["aanst_van"] == "1750-01-01"
    assert params["aanst_tot"] == "1770-12-31"
