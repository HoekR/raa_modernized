#!/usr/bin/env python3
"""Merge raa_staging into raa (preserves editorial.amendments, detects conflicts)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "api"))

from sqlalchemy import create_engine

from raa_api.config import database_url
from raa_api.editorial_merge import merge_release_into_raa


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Merge raa_staging → raa with editorial conflict detection")
    parser.add_argument("--release-id", default="dev")
    args = parser.parse_args()

    engine = create_engine(database_url())
    stats = merge_release_into_raa(engine, args.release_id)
    print(f"Merged staging → raa (release {args.release_id}): {stats['tables']} tables, {stats['conflicts']} conflict(s)")


if __name__ == "__main__":
    main()
