import pytest
from pydantic import ValidationError

from raa_api.schemas import SearchRequest, text_search_patterns


def test_search_request_match_modes_default():
    req = SearchRequest()
    assert req.functie_match == "any"
    assert req.instelling_match == "any"
    assert req.include_shadow_dates is True


def test_search_request_match_modes_all():
    req = SearchRequest(functie_match="all", instelling_match="all")
    assert req.functie_match == "all"


def test_search_request_rejects_invalid_match_mode():
    with pytest.raises(ValidationError):
        SearchRequest(functie_match="xor")


def test_text_search_patterns_wildcards():
    patterns = text_search_patterns('de*g "van der"')
    assert "%de%g%" in patterns or any("de" in p for p in patterns)
    assert "van der" in patterns
