"""Year histogram aggregation for search responses (D-UI-14d)."""

from __future__ import annotations

from collections import defaultdict

from raa_api.schemas import TimelineMeta, YearCount

DECADE_SPAN_THRESHOLD = 120

PERIOD_STACK_ORDER = ("me", "republiek", "batfra", "negentiende_eeuw")


def compress_timeline(rows: list[tuple[int, int]]) -> tuple[list[YearCount], str]:
    """Bin by year, or by decade when the dated span exceeds DECADE_SPAN_THRESHOLD."""
    if not rows:
        return [], "year"
    years = [int(y) for y, _ in rows]
    span = max(years) - min(years)
    if span <= DECADE_SPAN_THRESHOLD:
        return [YearCount(year=int(y), count=int(c)) for y, c in rows], "year"
    bins: dict[int, int] = defaultdict(int)
    for y, c in rows:
        decade = (int(y) // 10) * 10
        bins[decade] += int(c)
    return [YearCount(year=d, count=c) for d, c in sorted(bins.items())], "decade"


def compress_stacked_timeline(bins: list[YearCount]) -> tuple[list[YearCount], str]:
    """Decade compression for stacked period bins (sums segment counts per decade)."""
    if not bins:
        return [], "year"
    years = [b.year for b in bins]
    span = max(years) - min(years)
    if span <= DECADE_SPAN_THRESHOLD:
        return bins, "year"
    decade_map: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for b in bins:
        decade = (b.year // 10) * 10
        for key, value in b.by_period.items():
            decade_map[decade][key] += int(value)
    merged: list[YearCount] = []
    for decade in sorted(decade_map):
        by_period = dict(decade_map[decade])
        merged.append(
            YearCount(year=decade, count=sum(by_period.values()), by_period=by_period)
        )
    return merged, "decade"


def merge_period_year_rows(
    period_rows: dict[str, list[tuple[int, int]]],
) -> list[YearCount]:
    """Merge per-period (year, count) rows into stacked YearCount bins."""
    by_year: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for period_key, rows in period_rows.items():
        for y, count in rows:
            by_year[int(y)][period_key] = int(count)
    merged: list[YearCount] = []
    for year in sorted(by_year):
        segments = {k: int(v) for k, v in by_year[year].items()}
        merged.append(
            YearCount(year=year, count=sum(segments.values()), by_period=segments)
        )
    return merged
