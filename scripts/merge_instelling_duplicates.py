#!/usr/bin/env python3
"""Merge duplicate raa.instelling rows from a JSON plan.

Plan format (list):
  [{"keep": 33, "drop": [32], "keep_naam": "...", "drop_naam": ["..."], ...}, ...]

Dry-run by default; pass --apply to rewrite FKs and delete duplicates.

  uv run python scripts/merge_instelling_duplicates.py output/instelling_typo_duplicates.json
  uv run python scripts/merge_instelling_duplicates.py output/instelling_typo_duplicates.json --apply
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )


FK_UPDATES = (
    ("raa.aanstelling", "instelling_id"),
    ("raa.functie_instelling_span", "instelling_id"),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="JSON plan from typo scan")
    parser.add_argument("--apply", action="store_true", help="Write changes")
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    if not plan:
        print("Empty plan; nothing to do.")
        return

    print(f"Plan: {len(plan)} merge group(s) from {args.plan}\n")
    for g in plan:
        print(f"KEEP {g['keep']} (n={g.get('keep_n', '?')})  {g.get('keep_naam', '')}")
        for did, dnaam in zip(g["drop"], g.get("drop_naam", []), strict=False):
            print(f"  DROP {did}  {dnaam}")
        print()

    if not args.apply:
        print("Dry-run only. Re-run with --apply to rewrite FKs and delete duplicates.")
        return

    engine = create_engine(database_url())
    with engine.begin() as conn:
        for g in plan:
            keep = int(g["keep"])
            for dup in g["drop"]:
                dup = int(dup)
                for table, col in FK_UPDATES:
                    try:
                        n = conn.execute(
                            text(f"UPDATE {table} SET {col} = :keep WHERE {col} = :dup"),
                            {"keep": keep, "dup": dup},
                        ).rowcount
                        print(f"  {table}.{col}: {n} rows {dup} → {keep}")
                    except Exception as exc:  # noqa: BLE001
                        print(f"  skip {table}: {exc}")
                conn.execute(text("DELETE FROM raa.instelling WHERE id = :dup"), {"dup": dup})
                print(f"  deleted instelling {dup}")

    print("\nDone. Prefer re-import or span rebuild if counts look off.")


if __name__ == "__main__":
    main()
