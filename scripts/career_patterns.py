#!/usr/bin/env python3
"""Career pattern analysis CLI (sequences, transitions, F-RQ0 discontinuity).

Reads ``raa.aanstelling`` from Postgres and writes scratch parquet via data_io.

  uv run python scripts/career_patterns.py export-events
  uv run python scripts/career_patterns.py sequences
  uv run python scripts/career_patterns.py transitions --grain instelling
  uv run python scripts/career_patterns.py discontinuity
  uv run python scripts/career_patterns.py overview

Politics/influence RQ: docs/CAREER_RQS.md (F-RQ0).
Optional filters: --period republiek --year-min 1600 --year-max 1795
--drop-undated --min-posts 2
By default drops appointments missing functie_id or instelling_id
(--keep-incomplete-office to retain).
"""

from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import create_engine

from data_io import load, resolve, save_parquet
from raa_career_patterns import (
    PERIOD_FLAG_COLS,
    aggregate_matrix,
    build_sequences,
    events_for_export,
    filter_events,
    load_events,
    pairwise_transitions,
    sequences_for_export,
)
from raa_career_patterns.discontinuity import DEFAULT_WINDOWS, compare_windows
from raa_career_patterns.overview import format_overview_text


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--period",
        action="append",
        choices=list(PERIOD_FLAG_COLS),
        default=None,
        help="Keep rows with this period flag (repeatable; OR logic)",
    )
    parser.add_argument("--year-min", type=int, default=None)
    parser.add_argument("--year-max", type=int, default=None)
    parser.add_argument(
        "--drop-undated",
        action="store_true",
        help="Drop appointments without a usable van year",
    )
    parser.add_argument(
        "--min-posts",
        type=int,
        default=None,
        help="Keep only persons with at least N posts after other filters",
    )
    parser.add_argument(
        "--keep-incomplete-office",
        action="store_true",
        help="Keep appointments missing functie_id or instelling_id (default: drop)",
    )


def _apply_filters(events, args):
    return filter_events(
        events,
        period_flags=args.period,
        year_min=args.year_min,
        year_max=args.year_max,
        drop_undated=args.drop_undated,
        require_complete_office=not args.keep_incomplete_office,
        min_posts=args.min_posts,
    )


def cmd_export_events(args: argparse.Namespace) -> int:
    engine = create_engine(database_url())
    events = _apply_filters(load_events(engine), args)
    path = save_parquet(
        events_for_export(events),
        logical_name="career_events",
        script="scripts/career_patterns.py",
    )
    print(f"Wrote {len(events)} events → {path}")
    return 0


def cmd_sequences(args: argparse.Namespace) -> int:
    engine = create_engine(database_url())
    events = _apply_filters(load_events(engine), args)
    sequences = build_sequences(events)
    path = save_parquet(
        sequences_for_export(sequences),
        logical_name="career_sequences",
        script="scripts/career_patterns.py",
    )
    dated = int(sequences["seq_idx"].notna().sum())
    print(f"Wrote {len(sequences)} sequence rows ({dated} dated) → {path}")
    return 0


def cmd_transitions(args: argparse.Namespace) -> int:
    engine = create_engine(database_url())
    events = _apply_filters(load_events(engine), args)
    sequences = build_sequences(events)
    transitions = pairwise_transitions(sequences)
    matrix = aggregate_matrix(transitions, grain=args.grain)
    t_path = save_parquet(
        transitions,
        logical_name="career_transitions",
        script="scripts/career_patterns.py",
    )
    m_path = save_parquet(
        matrix,
        logical_name="career_transition_matrix",
        script="scripts/career_patterns.py",
    )
    kept = int((~transitions["skipped_overlap"]).sum()) if not transitions.empty else 0
    print(
        f"Wrote {len(transitions)} transitions "
        f"({kept} non-overlap) → {t_path}"
    )
    print(f"Wrote {len(matrix)} matrix rows (grain={args.grain}) → {m_path}")
    return 0


def cmd_discontinuity(args: argparse.Namespace) -> int:
    """F-RQ0: politics/influence continuity across wetsverzetting vs quiet cuts."""
    engine = create_engine(database_url())
    events = _apply_filters(load_events(engine), args)
    cuts = [c.strip() for c in args.cuts.split(",") if c.strip()]
    summary, crossings = compare_windows(events, cuts)
    s_path = save_parquet(
        summary,
        logical_name="career_discontinuity_summary",
        script="scripts/career_patterns.py",
    )
    c_path = save_parquet(
        crossings,
        logical_name="career_discontinuity_crossings",
        script="scripts/career_patterns.py",
    )
    print(summary.to_string(index=False))
    print(f"Wrote summary ({len(summary)} rows) → {s_path}")
    print(f"Wrote crossings ({len(crossings)} rows) → {c_path}")
    return 0


def cmd_overview(args: argparse.Namespace) -> int:
    """Print exploration overview from parquet (or rebuild from DB)."""
    if args.from_db:
        engine = create_engine(database_url())
        events = _apply_filters(load_events(engine), args)
        sequences = build_sequences(events)
        transitions = pairwise_transitions(sequences)
        cuts = [c.strip() for c in args.cuts.split(",") if c.strip()]
        summary, _crossings = compare_windows(events, cuts)
    else:
        for name in ("career_sequences", "career_transitions"):
            if not resolve(name).exists():
                print(
                    f"Missing {name}. Run sequences/transitions first, "
                    "or pass --from-db.",
                    file=sys.stderr,
                )
                return 1
        sequences = load("career_sequences")
        transitions = load("career_transitions")
        disc_path = resolve("career_discontinuity_summary")
        summary = load("career_discontinuity_summary") if disc_path.exists() else None
        if summary is None and args.with_discontinuity:
            engine = create_engine(database_url())
            events = _apply_filters(load_events(engine), args)
            cuts = [c.strip() for c in args.cuts.split(",") if c.strip()]
            summary, crossings = compare_windows(events, cuts)
            save_parquet(
                summary,
                logical_name="career_discontinuity_summary",
                script="scripts/career_patterns.py",
            )
            save_parquet(
                crossings,
                logical_name="career_discontinuity_crossings",
                script="scripts/career_patterns.py",
            )

    text = format_overview_text(
        sequences, transitions, discontinuity_summary=summary
    )
    print(text)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_events = sub.add_parser("export-events", help="Export normalized career events")
    _add_filter_args(p_events)
    p_events.set_defaults(func=cmd_export_events)

    p_seq = sub.add_parser("sequences", help="Build per-person sequences")
    _add_filter_args(p_seq)
    p_seq.set_defaults(func=cmd_sequences)

    p_trans = sub.add_parser("transitions", help="Pairwise transitions + matrix")
    _add_filter_args(p_trans)
    p_trans.add_argument(
        "--grain",
        choices=["functie", "instelling", "office"],
        default="instelling",
        help="Aggregation grain for the transition matrix (default: instelling)",
    )
    p_trans.set_defaults(func=cmd_transitions)

    p_disc = sub.add_parser(
        "discontinuity",
        help="F-RQ0: influence-layer continuity across cut vs quiet windows",
    )
    _add_filter_args(p_disc)
    p_disc.add_argument(
        "--cuts",
        default=",".join(DEFAULT_WINDOWS.keys()),
        help=f"Comma-separated window labels (default: {','.join(DEFAULT_WINDOWS)})",
    )
    p_disc.set_defaults(func=cmd_discontinuity)

    p_ov = sub.add_parser(
        "overview",
        help="Print corpus overview for exploration (from parquet or --from-db)",
    )
    _add_filter_args(p_ov)
    p_ov.add_argument(
        "--from-db",
        action="store_true",
        help="Rebuild sequences/transitions from Postgres instead of parquet",
    )
    p_ov.add_argument(
        "--with-discontinuity",
        action="store_true",
        help="Compute F-RQ0 if career_discontinuity_summary.parquet is missing",
    )
    p_ov.add_argument(
        "--cuts",
        default=",".join(DEFAULT_WINDOWS.keys()),
        help=f"Window labels when computing discontinuity (default: {','.join(DEFAULT_WINDOWS)})",
    )
    p_ov.set_defaults(func=cmd_overview)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
