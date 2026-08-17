"""Personen wildcard q parsing and search WHERE construction."""

from __future__ import annotations

from unittest.mock import MagicMock

from raa_api.schemas import SearchRequest, text_search_patterns
from raa_api.search import _persoon_where, search_personen


def test_text_search_patterns_gansne_question_mark():
    assert text_search_patterns("gansne?") == ["gansne_"]


def test_text_search_patterns_gansne_star():
    assert text_search_patterns("gansne*") == ["gansne%"]


def test_text_search_patterns_wasse_star():
    assert text_search_patterns("wasse*") == ["wasse%"]


def test_persoon_where_wildcard_q_sets_ilike_param():
    req = SearchRequest(q="wasse*", period="republiek", period_mode="scoped")
    where, params = _persoon_where(req)
    assert "q0" in params
    assert params["q0"] == "wasse%"
    assert "ILIKE :q0" in where


def test_persoon_text_clause_searches_legacy_when_display_set():
    from raa_api.search import _persoon_text_token_clause

    clause = _persoon_text_token_clause("q0")
    assert "search_display IS NULL" not in clause
    assert "geslachtsnaam ILIKE :q0" in clause


def test_search_personen_wildcard_returns_stable_total():
    """Regression: wildcard q must not error; total/hits reflect DB mock."""
    db = MagicMock()
    # COUNT(*), then facet COUNTs may call scalar repeatedly
    db.execute.return_value.scalar.side_effect = [12, 12, 0, 0, 0, 0, 0, 0]
    db.execute.return_value.mappings.return_value.all.return_value = [
        {
            "id": 1,
            "voornaam": "Jan",
            "tussenvoegsel": "",
            "geslachtsnaam": "Wassen",
            "geboortedatum_als_bekend": "1700",
            "overlijdensdatum_als_bekend": None,
            "searchable": "wassen jan",
            "geboorte_edtf": None,
            "overlijden_edtf": None,
            "life_start_year": None,
            "life_end_year": None,
            "life_start_source": None,
            "life_end_source": None,
            "adellijke_titel": None,
            "academische_titel": None,
        }
    ]
    db.execute.return_value.all.return_value = []

    resp = search_personen(
        db,
        SearchRequest(q="wasse*", period="republiek", period_mode="scoped", size=100),
    )
    assert resp.total == 12
    assert len(resp.hits) == 1
    assert resp.hits[0]["geslachtsnaam"] == "Wassen"

    first_params = db.execute.call_args_list[0][0][1]
    assert first_params["q0"] == "wasse%"
