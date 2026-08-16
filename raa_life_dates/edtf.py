"""EDTF Level 1 subset: derive stored strings and parse query intervals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

_YEAR_RE = re.compile(r"^(-?\d{1,4})([~?%]?)$")
_INTERVAL_RE = re.compile(r"^(.+?)/(.+)$")


@dataclass(frozen=True)
class YearInterval:
    start: int | None
    end: int | None

    def overlaps(self, other: YearInterval) -> bool:
        a0 = self.start if self.start is not None else -10_000
        a1 = self.end if self.end is not None else 10_000
        b0 = other.start if other.start is not None else -10_000
        b1 = other.end if other.end is not None else 10_000
        return a0 <= b1 and b0 <= a1


def _is_truthy_flag(value: Any) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes"}
    return bool(value)


def _year_from_iso_date(value: Any) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nat", "none"}:
        return None
    try:
        return int(pd.Period(text, freq="D").year)
    except (ValueError, TypeError):
        return None


def _year_from_parts(
    year: Any,
    month: Any = None,
    day: Any = None,
    approximate: bool = False,
) -> tuple[str | None, int | None]:
    if year is None or (isinstance(year, float) and pd.isna(year)):
        return None, None
    year_text = str(year).strip().replace(".0", "")
    if not year_text:
        return None, None
    qualifier = "~" if approximate else ""
    try:
        y = int(float(year_text))
    except ValueError:
        return None, None

    month_val: int | None = None
    day_val: int | None = None
    if month is not None and not (isinstance(month, float) and pd.isna(month)):
        try:
            month_val = int(month)
        except (ValueError, TypeError):
            month_val = None
    if day is not None and not (isinstance(day, float) and pd.isna(day)):
        try:
            day_val = int(day)
        except (ValueError, TypeError):
            day_val = None

    if month_val and day_val:
        return f"{y:04d}-{month_val:02d}-{day_val:02d}{qualifier}", y
    if month_val:
        return f"{y:04d}-{month_val:02d}{qualifier}", y
    return f"{y}{qualifier}", y


def derive_life_edtf(row: pd.Series) -> tuple[str | None, str | None, int | None, int | None]:
    """Return (geboorte_edtf, overlijden_edtf, geboorte_year, overlijden_year)."""
    geboorte_edtf: str | None = None
    overlijden_edtf: str | None = None
    geboorte_year = _year_from_iso_date(row.get("geboortedatum"))
    overlijden_year = _year_from_iso_date(row.get("overlijdensdatum"))

    if geboorte_year is None:
        geboorte_edtf, geboorte_year = _year_from_parts(
            row.get("geboortejaar"),
            row.get("geboortemaand"),
            row.get("geboortedag"),
            approximate=_is_truthy_flag(row.get("onbepaaldgeboortedatum")),
        )
    else:
        approx = _is_truthy_flag(row.get("onbepaaldgeboortedatum"))
        geboorte_edtf = str(row.get("geboortedatum_als_bekend") or "").strip() or None
        if geboorte_edtf and approx and not geboorte_edtf.endswith(("~", "?", "%")):
            geboorte_edtf = f"{geboorte_edtf}~"

    if overlijden_year is None:
        overlijden_edtf, overlijden_year = _year_from_parts(
            row.get("overlijdensjaar"),
            row.get("overlijdensmaand"),
            row.get("overlijdensdag"),
            approximate=_is_truthy_flag(row.get("onbepaaldoverlijdensdatum")),
        )
    else:
        approx = _is_truthy_flag(row.get("onbepaaldoverlijdensdatum"))
        overlijden_edtf = str(row.get("overlijdensdatum_als_bekend") or "").strip() or None
        if overlijden_edtf and approx and not overlijden_edtf.endswith(("~", "?", "%")):
            overlijden_edtf = f"{overlijden_edtf}~"

    return geboorte_edtf, overlijden_edtf, geboorte_year, overlijden_year


def _parse_edtf_point(token: str) -> int | None:
    token = token.strip()
    if not token or token == "..":
        return None
    match = _YEAR_RE.match(token)
    if not match:
        raise ValueError(f"Unsupported EDTF point: {token!r}")
    return int(match.group(1))


def parse_edtf_interval(value: str) -> YearInterval:
    """Parse Level 1 EDTF interval or point expressions into inclusive year bounds."""
    text = value.strip()
    if not text:
        raise ValueError("Empty EDTF interval")

    if text.startswith("../"):
        return YearInterval(start=None, end=_parse_edtf_point(text[3:]))
    if text.startswith("/") and not text.startswith("//"):
        return YearInterval(start=None, end=_parse_edtf_point(text[1:]))
    if text.endswith("/.."):
        return YearInterval(start=_parse_edtf_point(text[:-3]), end=None)
    if text.endswith("/") and "/" not in text[:-1]:
        return YearInterval(start=_parse_edtf_point(text[:-1]), end=None)

    match = _INTERVAL_RE.match(text)
    if match:
        left, right = match.group(1).strip(), match.group(2).strip()
        if right == "..":
            return YearInterval(start=_parse_edtf_point(left), end=None)
        if left in {"", ".."}:
            return YearInterval(start=None, end=_parse_edtf_point(right))
        return YearInterval(start=_parse_edtf_point(left), end=_parse_edtf_point(right))

    return YearInterval(start=_parse_edtf_point(text), end=_parse_edtf_point(text))
