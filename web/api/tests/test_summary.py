"""Summary endpoints return aggregates without hit rows."""

from __future__ import annotations

from unittest.mock import MagicMock

from raa_api.schemas import SearchRequest, SummaryResponse
from raa_api.search import summarize_aanstellingen, summarize_personen


def test_summarize_personen_no_hits_field():
    db = MagicMock()
    db.execute.return_value.scalar.return_value = 42
    db.execute.return_value.all.return_value = []
    db.execute.return_value.mappings.return_value.all.return_value = []

    resp = summarize_personen(db, SearchRequest(q="test", period="republiek"))
    assert isinstance(resp, SummaryResponse)
    assert resp.total == 42
    assert isinstance(resp.facets, dict)
    assert not hasattr(resp, "hits") or "hits" not in resp.model_dump()


def test_summarize_aanstellingen_no_hits_field():
    db = MagicMock()
    db.execute.return_value.scalar.return_value = 7
    db.execute.return_value.all.return_value = []
    db.execute.return_value.mappings.return_value.all.return_value = []

    resp = summarize_aanstellingen(db, SearchRequest(period="republiek"))
    assert isinstance(resp, SummaryResponse)
    assert resp.total == 7
    assert isinstance(resp.facets, dict)
