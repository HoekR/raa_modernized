"""Tests for exact date part validation."""

from __future__ import annotations

import pytest

from raa_api.editorial_dates import (
    sanitize_life_day,
    sanitize_life_month,
    validate_date_event_parts,
    validate_persoon_date_values,
)


def test_sanitize_life_month_empty():
    assert sanitize_life_month("", field="geboortemaand") == ""


def test_sanitize_life_month_valid():
    assert sanitize_life_month("3", field="geboortemaand") == "3"


def test_sanitize_life_month_invalid():
    with pytest.raises(ValueError, match="Month out of range"):
        sanitize_life_month("13", field="geboortemaand")


def test_validate_day_without_month():
    with pytest.raises(ValueError, match="dag zonder maand"):
        validate_date_event_parts(year="1701", month=None, day="15", label="geboorte")


def test_validate_month_without_year():
    with pytest.raises(ValueError, match="zonder jaar"):
        validate_date_event_parts(year=None, month="3", day=None, label="geboorte")


def test_validate_invalid_calendar_day():
    with pytest.raises(ValueError, match="ongeldige dag"):
        validate_date_event_parts(year="1701", month="2", day="31", label="geboorte")


def test_validate_persoon_year_only_ok():
    validate_persoon_date_values(
        {
            "geboortejaar": "1701",
            "geboortemaand": "",
            "geboortedag": "",
            "overlijdensjaar": "1750",
            "overlijdensmaand": "",
            "overlijdensdag": "",
        }
    )


def test_sanitize_life_day_valid():
    assert sanitize_life_day("15", field="geboortedag") == "15"
