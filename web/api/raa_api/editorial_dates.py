"""Exact life-date parts for editorial (y required; m/d optional)."""

from __future__ import annotations

import calendar
from typing import Any

from raa_life_dates.validate import is_plausible_life_year

DATE_EVENTS: dict[str, tuple[str, str, str]] = {
    "geboorte": ("geboortejaar", "geboortemaand", "geboortedag"),
    "overlijden": ("overlijdensjaar", "overlijdensmaand", "overlijdensdag"),
}

ALL_DATE_PART_FIELDS: frozenset[str] = frozenset(
    field for parts in DATE_EVENTS.values() for field in parts
)


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text.replace(".0", "")))
    except ValueError:
        return None


def sanitize_life_month(value: str | None, *, field: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    try:
        month = int(float(text.replace(".0", "")))
    except ValueError as exc:
        raise ValueError(f"Invalid month for {field}: {value!r}") from exc
    if not 1 <= month <= 12:
        raise ValueError(f"Month out of range for {field}: {month}")
    return str(month)


def sanitize_life_day(value: str | None, *, field: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    try:
        day = int(float(text.replace(".0", "")))
    except ValueError as exc:
        raise ValueError(f"Invalid day for {field}: {value!r}") from exc
    if not 1 <= day <= 31:
        raise ValueError(f"Day out of range for {field}: {day}")
    return str(day)


def validate_date_event_parts(
    *,
    year: str | None,
    month: str | None,
    day: str | None,
    label: str,
) -> None:
    y = _parse_optional_int(year)
    m = _parse_optional_int(month)
    d = _parse_optional_int(day)

    if d is not None and m is None:
        raise ValueError(f"{label}: dag zonder maand")
    if (m is not None or d is not None) and y is None:
        raise ValueError(f"{label}: maand/dag zonder jaar")
    if y is not None and not is_plausible_life_year(y):
        raise ValueError(f"{label}: jaar buiten bereik ({y})")
    if y is not None and m is not None and d is not None:
        last = calendar.monthrange(y, m)[1]
        if d > last:
            raise ValueError(f"{label}: ongeldige dag {d:02d}-{m:02d}-{y}")


def validate_persoon_date_values(values: dict[str, Any]) -> None:
    """Validate geboorte/overlijden y-m-d triplets from effective field values."""
    for label, (year_f, month_f, day_f) in DATE_EVENTS.items():
        validate_date_event_parts(
            year=_cell(values.get(year_f)),
            month=_cell(values.get(month_f)),
            day=_cell(values.get(day_f)),
            label=label,
        )


def _cell(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
