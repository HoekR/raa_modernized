#!/usr/bin/env python3
"""Merge duplicate Staten-Generaal instelling rows (RS E2).

Picks the canonical id (most aanstellingen), rewrites FKs, deletes duplicates.

Dry-run by default; pass --apply to write.
"""

from __future__ import annotations

import argparse
import os

from sqlalchemy import create_engine, text


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )


def find_candidates(conn):
    return conn.execute(
        text(
            """
            SELECT i.id, i.naam, COUNT(a.id) AS aanstellingen
            FROM raa.instelling i
            LEFT JOIN raa.aanstelling a ON a.instelling_id = i.id
            WHERE i.naam ILIKE '%staten%generaal%'
            GROUP BY i.id, i.naam
            ORDER BY COUNT(a.id) DESC, i.id
            """
        )
    ).mappings().all()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    parser.add_argument(
        "--keep",
        type=int,
        default=None,
        help="Canonical instelling id to keep (default: most aanstellingen)",
    )
    args = parser.parse_args()

    engine = create_engine(database_url())
    with engine.connect() as conn:
        rows = find_candidates(conn)
        if len(rows) < 2:
            print("Fewer than 2 Staten-Generaal rows; nothing to merge.")
            for r in rows:
                print(f"  {r['id']}: {r['naam']} ({r['aanstellingen']} aanstellingen)")
            return

        print("Candidates:")
        for r in rows:
            print(f"  {r['id']}: {r['naam']} ({r['aanstellingen']} aanstellingen)")

        keep = args.keep or int(rows[0]["id"])
        drop = [int(r["id"]) for r in rows if int(r["id"]) != keep]
        if not drop:
            print("Keep id not in candidates.")
            return

        print(f"Keep {keep}; drop {drop}")
        if not args.apply:
            print("Dry-run only. Re-run with --apply to rewrite FKs and delete duplicates.")
            return

    with engine.begin() as conn:
        for dup in drop:
            n = conn.execute(
                text("UPDATE raa.aanstelling SET instelling_id = :keep WHERE instelling_id = :dup"),
                {"keep": keep, "dup": dup},
            ).rowcount
            print(f"  aanstelling: {n} rows → {keep}")
            try:
                n2 = conn.execute(
                    text(
                        "UPDATE raa.functie_instelling_span "
                        "SET instelling_id = :keep WHERE instelling_id = :dup"
                    ),
                    {"keep": keep, "dup": dup},
                ).rowcount
                print(f"  functie_instelling_span: {n2} rows → {keep}")
            except Exception as exc:  # noqa: BLE001
                print(f"  skip functie_instelling_span: {exc}")
            conn.execute(text("DELETE FROM raa.instelling WHERE id = :dup"), {"dup": dup})
            print(f"  deleted instelling {dup}")

        print("Done. Prefer re-import or rebuild spans for clean counts.")


if __name__ == "__main__":
    main()
