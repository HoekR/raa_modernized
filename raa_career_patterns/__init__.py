"""Career pattern analysis: sequences, transitions, politics/influence RQs."""

from raa_career_patterns.circulation import (
    circulation_by_era,
    filter_dense_circulation,
    node_flow_by_era,
    top_dense_edges_by_era,
)
from raa_career_patterns.discontinuity import (
    DEFAULT_WINDOWS,
    classify_crossings,
    compare_windows,
    influence_layer,
    summarize_window,
)
from raa_career_patterns.overview import format_overview_text
from raa_career_patterns.events import (
    PERIOD_FLAG_COLS,
    events_for_export,
    load_events,
    normalize_events,
)
from raa_career_patterns.filters import filter_events
from raa_career_patterns.sequences import (
    build_sequences,
    collapse_consecutive_offices,
    intervals_overlap,
    sequences_for_export,
)
from raa_career_patterns.transitions import aggregate_matrix, pairwise_transitions

__all__ = [
    "DEFAULT_WINDOWS",
    "PERIOD_FLAG_COLS",
    "aggregate_matrix",
    "build_sequences",
    "circulation_by_era",
    "classify_crossings",
    "collapse_consecutive_offices",
    "compare_windows",
    "events_for_export",
    "filter_dense_circulation",
    "filter_events",
    "format_overview_text",
    "influence_layer",
    "intervals_overlap",
    "load_events",
    "node_flow_by_era",
    "normalize_events",
    "pairwise_transitions",
    "sequences_for_export",
    "summarize_window",
    "top_dense_edges_by_era",
]
