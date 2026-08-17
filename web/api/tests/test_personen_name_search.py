"""Personen q_mode and structured name-part filters."""

from __future__ import annotations

from raa_api.schemas import SearchRequest, text_search_patterns
from raa_api.search import _persoon_where


def test_text_search_patterns_prefix_anchor():
    assert text_search_patterns("aylva", anchor="prefix") == ["aylva%"]
    assert text_search_patterns("wasse*", anchor="prefix") == ["wasse%"]


def test_persoon_where_q_mode_prefix():
    req = SearchRequest(q="aylva", q_mode="prefix", period="republiek")
    _, params = _persoon_where(req)
    assert params["q0"] == "aylva%"


def test_persoon_where_q_mode_contains():
    req = SearchRequest(q="aylva", q_mode="contains", period="republiek")
    _, params = _persoon_where(req)
    assert params["q0"] == "%aylva%"


def test_persoon_where_q_mode_exact():
    req = SearchRequest(q="Aylva", q_mode="exact", period="republiek")
    _, params = _persoon_where(req)
    assert params["q0"] == "aylva"


def test_text_search_patterns_exact_anchor():
    assert text_search_patterns("Aylva", anchor="exact") == ["aylva"]
    assert text_search_patterns("wasse*", anchor="exact") == ["wasse*"]


def test_persoon_name_part_geslachtsnaam():
    req = SearchRequest(
        period="republiek",
        filters={"geslachtsnaam": ["Ayl*"], "voornaam": ["Tjaerd"]},
    )
    where, params = _persoon_where(req)
    assert "p.geslachtsnaam ILIKE" in where
    assert "p.voornaam ILIKE" in where
    assert any(v == "ayl%" for v in params.values())
    assert any(v == "tjaerd%" for v in params.values())


def test_persoon_name_part_alias():
    req = SearchRequest(period="republiek", filters={"alias": ["Pieter"]})
    where, _ = _persoon_where(req)
    assert "raa.alias" in where
