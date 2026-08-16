#!/usr/bin/env python3
"""Print pilot baseline counts for docs/VALIDATION_RQS.md (requires Postgres + imported data)."""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
)

# Period clause for republiek (incl. republiek_friezen) — mirrors search.py
REPUBLIEK_WHERE = "(p.republiek = 1 OR p.republiek_friezen = 1)"
REPUBLIEK_A = "(a.republiek = 1 OR a.republiek_friezen = 1)"
REPUBLIEK_I = "(i.republiek = 1 OR i.republiek_friezen = 1)"
REPUBLIEK_F = "(f.republiek = 1 OR f.republiek_friezen = 1)"


def main() -> None:
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM raa.persoon LIMIT 1"))
    except Exception as exc:
        print(f"Cannot reach Postgres ({DATABASE_URL}): {exc}", file=sys.stderr)
        sys.exit(1)

    queries: list[tuple[str, str, str]] = [
        (
            "P1",
            "personen",
            f"""
            SELECT COUNT(*) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND COALESCE(p.search_display, p.searchable, '') ILIKE '%aylva%'
            """,
        ),
        (
            "P2",
            "personen",
            f"""
            SELECT COUNT(*) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND COALESCE(p.geboorte_year, p.life_start_year) IS NOT NULL
              AND COALESCE(p.geboorte_year, p.life_start_year) >= 1700
              AND COALESCE(p.geboorte_year, p.life_start_year) <= 1750
            """,
        ),
        (
            "P3",
            "personen",
            f"""
            SELECT COUNT(DISTINCT p.id) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND EXISTS (
                SELECT 1 FROM raa.aanstelling a
                WHERE a.persoon_id = p.id AND {REPUBLIEK_A}
                  AND a.functie_id = 561 AND a.instelling_id = 171
              )
            """,
        ),
        (
            "A1",
            "aanstellingen",
            f"""
            SELECT COUNT(*) FROM raa.aanstelling a
            WHERE {REPUBLIEK_A} AND a.functie_id = 561 AND a.instelling_id = 171
            """,
        ),
        (
            "I1",
            "instellingen",
            f"""
            SELECT COUNT(*) FROM raa.instelling i
            WHERE {REPUBLIEK_I} AND i.naam ILIKE 'staten%friesland'
            """,
        ),
        (
            "F1",
            "functies",
            f"""
            SELECT COUNT(*) FROM raa.functie f
            WHERE {REPUBLIEK_F} AND f.naam ILIKE '%gedeputeerde%'
            """,
        ),
    ]

    print("Pilot baseline counts (validation_rq_smoke)")
    print("-" * 40)
    with engine.connect() as conn:
        for case_id, entity, sql in queries:
            total = int(conn.execute(text(sql)).scalar() or 0)
            print(f"{case_id:4} {entity:14} total={total}")


if __name__ == "__main__":
    main()
