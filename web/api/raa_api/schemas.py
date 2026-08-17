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
    sort_dir: str = Field(default="asc", pattern="^(asc|desc)$")
    group_by: str | None = Field(default=None, pattern="^(instelling|functie)$")
    functie_match: str = Field(default="any", pattern="^(any|all)$")
    instelling_match: str = Field(default="any", pattern="^(any|all)$")
    include_shadow_dates: bool = True
    q_mode: str = Field(default="prefix", pattern="^(prefix|contains|pattern|exact)$")


class FacetValue(BaseModel):
    key: str
    label: str
    count: int


class YearCount(BaseModel):
    year: int
    count: int
    by_period: dict[str, int] = Field(default_factory=dict)


class TimelineMeta(BaseModel):
    field: str
    bin: str = "year"
    undated: int = 0
    stacked: bool = False


class SearchResponse(BaseModel):
    hits: list[dict[str, Any]]
    total: int
    facets: dict[str, list[FacetValue]] = Field(default_factory=dict)
    timeline: list[YearCount] = Field(default_factory=list)
    timeline_meta: TimelineMeta | None = None


class SummaryResponse(BaseModel):
    """Aggregates for charts (overview / Samenvatting) — no result rows."""

    total: int
    facets: dict[str, list[FacetValue]] = Field(default_factory=dict)
    timeline: list[YearCount] = Field(default_factory=list)
    timeline_meta: TimelineMeta | None = None


class PeriodCount(BaseModel):
    key: str
    label: str
    count: int


class AmendmentCreate(BaseModel):
    entity_type: str
    entity_id: int
    field: str
    value: str
    note: str | None = None


class AmendmentResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    field: str
    value: str | None
    editor_id: str
    note: str | None = None
    status: str
    created_at: Any = None
    updated_at: Any = None


class ConflictResolve(BaseModel):
    resolution: str = Field(pattern="^(keep_amendment|accept_base)$")


class BatchAmendmentChange(BaseModel):
    entity_type: str
    entity_id: int
    field: str
    value: str = ""


class BatchAmendmentRequest(BaseModel):
    changes: list[BatchAmendmentChange]
    note: str | None = None


def escape_like(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def text_search_patterns(query_string: str, *, anchor: str = "contains") -> list[str]:
    """Port legacy RAA wildcard semantics to SQL ILIKE patterns.

    anchor: prefix, contains, pattern (legacy wrap), or exact (whole-field ILIKE).
    """
    q = query_string.lower()
    quoted = [part[1:-1] for part in quoted_strings_re.findall(q)]
    q = quoted_strings_re.sub("", q)
    parts = [p for p in q.split() if p]
    patterns: list[str] = []
    for part in parts:
        part = escape_like(part)
        if anchor == "exact":
            patterns.append(part)
            continue
        part = part.replace("?", "_").replace("*", "%")
        if "%" not in part and "_" not in part:
            if anchor == "prefix":
                part = f"{part}%"
            elif anchor == "contains":
                part = f"%{part}%"
            else:
                part = f"%{part}%"
        patterns.append(part)
    for part in quoted:
        patterns.append(escape_like(part.lower()))
    return patterns
