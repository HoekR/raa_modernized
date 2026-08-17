"""Tests for editorial merge conflict detection."""

from __future__ import annotations

from raa_api.editorial import sanitize_field_value
from raa_api.editorial_merge import _norm


def test_norm_empty():
    assert _norm(None) is None
    assert _norm("") is None
    assert _norm("  x  ") == "x"


def test_sanitize_life_year_valid():
    assert sanitize_field_value("persoon", "geboortejaar", "1750") == "1750"


def test_sanitize_life_year_invalid():
    import pytest

    with pytest.raises(ValueError):
        sanitize_field_value("persoon", "geboortejaar", "10")
