from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

quoted_strings_re = re.compile(r'"[^"]+"')


class SearchRequest(BaseModel):
    model_config = {"populate_by_name": True}

    q: str | None = None
    period: str | None = None
    period_mode: str = Field(default="scoped", pattern="^(scoped|overall)$")
    filters: dict[str, list[str]] = Field(default_factory=dict)
    from_: int = Field(default=0, alias="from")
    size: int = Field(default=20, ge=1, le=100)
    sort: str = "geslachtsnaam"
    group_by: str | None = Field(default=None, pattern="^(instelling|functie)$")


class FacetValue(BaseModel):
    key: str
    label: str
    count: int


class SearchResponse(BaseModel):
    hits: list[dict[str, Any]]
    total: int
    facets: dict[str, list[FacetValue]] = Field(default_factory=dict)


class PeriodCount(BaseModel):
    key: str
    label: str
    count: int


def escape_like(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def text_search_patterns(query_string: str) -> list[str]:
    """Port legacy RAA wildcard semantics to SQL ILIKE patterns."""
    q = query_string.lower()
    quoted = [part[1:-1] for part in quoted_strings_re.findall(q)]
    q = quoted_strings_re.sub("", q)
    parts = [p for p in q.split() if p]
    patterns: list[str] = []
    for part in parts:
        part = escape_like(part)
        part = part.replace("?", "_").replace("*", "%")
        if "%" not in part and "_" not in part:
            part = f"%{part}%"
        patterns.append(part)
    for part in quoted:
        patterns.append(escape_like(part.lower()))
    return patterns
