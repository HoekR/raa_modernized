#!/usr/bin/env python3
"""Create editorial.* schema in Postgres (safe to re-run)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "web" / "api"))

from raa_api.db import SessionLocal  # noqa: E402
from raa_api.editorial import ensure_editorial_schema  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        ensure_editorial_schema(db)
        print("Editorial schema ready (editorial.amendments).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
