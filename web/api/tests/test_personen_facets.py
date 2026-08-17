"""Personen search returns live facet buckets."""

from __future__ import annotations

from unittest.mock import MagicMock

from raa_api.schemas import SearchRequest
from raa_api.search import _personen_facets, search_personen


def test_personen_facets_keys_include_geo_and_roles():
    """Facet helper returns expected dimension keys (empty DB → empty lists)."""
    db = MagicMock()
    # COUNT / GROUP BY queries → empty
    db.execute.return_value.all.return_value = []
    db.execute.return_value.scalar.return_value = 0

    req = SearchRequest(period="republiek", period_mode="scoped", filters={})
    facets = _personen_facets(db, "1=1", {}, req)
    assert set(facets) >= {
        "stand",
        "functie",
        "instelling",
        "provincie",
        "regio",
        "lokaal",
    }


def test_search_personen_includes_facets_shape(monkeypatch):
    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.mappings.return_value.all.return_value = []
    db.execute.return_value.all.return_value = []

    resp = search_personen(db, SearchRequest(q="aylva", period="republiek"))
    assert resp.total == 0
    assert isinstance(resp.facets, dict)
