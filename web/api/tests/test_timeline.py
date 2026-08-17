from raa_api.schemas import YearCount
from raa_api.search import _aanstelling_van_year_sql
from raa_api.timeline import (
    DECADE_SPAN_THRESHOLD,
    compress_stacked_timeline,
    compress_timeline,
    merge_period_year_rows,
)


def test_compress_timeline_year_bins():
    rows = [(1748, 3), (1749, 5), (1750, 2)]
    timeline, bin_mode = compress_timeline(rows)
    assert bin_mode == "year"
    assert len(timeline) == 3
    assert timeline[0].year == 1748


def test_compress_timeline_decade_bins_when_span_wide():
    rows = [(1500, 1), (1700, 2), (1850, 4)]
    timeline, bin_mode = compress_timeline(rows)
    assert bin_mode == "decade"
    assert [b.year for b in timeline] == [1500, 1700, 1850]


def test_merge_period_year_rows():
    merged = merge_period_year_rows(
        {
            "me": [(1580, 2)],
            "republiek": [(1580, 1), (1600, 5)],
        }
    )
    assert len(merged) == 2
    y1580 = next(b for b in merged if b.year == 1580)
    assert y1580.by_period == {"me": 2, "republiek": 1}
    assert y1580.count == 3


def test_compress_stacked_timeline_decade():
    bins = [
        YearCount(year=1505, count=1, by_period={"me": 1}),
        YearCount(year=1850, count=2, by_period={"negentiende_eeuw": 2}),
    ]
    timeline, bin_mode = compress_stacked_timeline(bins)
    assert bin_mode == "decade"


def test_decade_threshold():
    assert DECADE_SPAN_THRESHOLD == 120


def test_aanstelling_van_year_sql_parses_text_column():
    sql = _aanstelling_van_year_sql("a")
    assert "a.van" in sql
    assert "SUBSTRING" in sql
    assert "'None'" in sql
