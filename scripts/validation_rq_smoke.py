#!/usr/bin/env python3
"""Pilot baseline counts + cross-cutting X checks for docs/VALIDATION_RQS.md.

Requires Postgres with imported data.

  uv run python scripts/validation_rq_smoke.py
  uv run python scripts/validation_rq_smoke.py --assert   # fail if baselines drift
"""

from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
)

REPUBLIEK_WHERE = "(p.republiek = 1 OR p.republiek_friezen = 1)"
REPUBLIEK_A = "(a.republiek = 1 OR a.republiek_friezen = 1)"
REPUBLIEK_I = "(i.republiek = 1 OR i.republiek_friezen = 1)"
REPUBLIEK_F = "(f.republiek = 1 OR f.republiek_friezen = 1)"

# Captured 2026-07-17 against local pilot after B2f/B3e.
EXPECTED_RQ: dict[str, int] = {
    "P1": 37,
    "P2": 1616,
    "P3": 411,
    "A1": 677,
    "I1": 1,
    "F1": 3,
}


def _scalar(conn, sql: str, params: dict | None = None) -> int:
    return int(conn.execute(text(sql), params or {}).scalar() or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assert",
        dest="do_assert",
        action="store_true",
        help="Exit non-zero if RQ baselines drift or an X check fails",
    )
    args = parser.parse_args()

    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM raa.persoon LIMIT 1"))
    except Exception as exc:
        print(f"Cannot reach Postgres ({DATABASE_URL}): {exc}", file=sys.stderr)
        sys.exit(1)

    rq_queries: list[tuple[str, str, str]] = [
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

    failures: list[str] = []
    print("Pilot baseline counts (validation_rq_smoke)")
    print("-" * 40)
    with engine.connect() as conn:
        for case_id, entity, sql in rq_queries:
            total = _scalar(conn, sql)
            expected = EXPECTED_RQ.get(case_id)
            flag = ""
            if expected is not None and total != expected:
                flag = f"  !! expected {expected}"
                failures.append(f"{case_id}: got {total}, expected {expected}")
            print(f"{case_id:4} {entity:14} total={total}{flag}")

        print()
        print("Cross-cutting X checks (pilot)")
        print("-" * 40)

        # X1: Republiek search includes republiek_friezen-only persons
        friezen_only = _scalar(
            conn,
            """
            SELECT COUNT(*) FROM raa.persoon p
            WHERE p.republiek_friezen = 1 AND COALESCE(p.republiek, 0) = 0
            """,
        )
        friezen_in_republiek = _scalar(
            conn,
            f"""
            SELECT COUNT(*) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND p.republiek_friezen = 1 AND COALESCE(p.republiek, 0) = 0
            """,
        )
        x1_ok = friezen_only > 0 and friezen_only == friezen_in_republiek
        print(
            f"X1   republiek_friezen in Republiek: "
            f"friezen_only={friezen_only} matched={friezen_in_republiek} "
            f"{'PASS' if x1_ok else 'FAIL'}"
        )
        if not x1_ok:
            failures.append("X1: republiek_friezen rows not fully included in Republiek")

        # X2: wildcard patterns expand recall vs plain token
        plain = _scalar(
            conn,
            f"""
            SELECT COUNT(*) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND COALESCE(p.search_display, p.searchable, '') ILIKE '%aylva%'
            """,
        )
        wild = _scalar(
            conn,
            f"""
            SELECT COUNT(*) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND COALESCE(p.search_display, p.searchable, '') ILIKE 'van%aylva'
            """,
        )
        x2_ok = plain > 0 and wild > 0 and wild <= plain
        print(f"X2   wildcard aylva={plain} van*aylva={wild} {'PASS' if x2_ok else 'FAIL'}")
        if not x2_ok:
            failures.append("X2: wildcard semantics unexpected")

        # X3: Tjaerd van Aylva pilot id 21009
        row = conn.execute(
            text(
                """
                SELECT id, voornaam, geslachtsnaam,
                       COALESCE(search_display, '') AS search_display
                FROM raa.persoon WHERE id = 21009
                """
            )
        ).mappings().first()
        x3_ok = bool(
            row
            and row["voornaam"] == "Tjaerd"
            and row["geslachtsnaam"] == "Aylva"
            and "aylva" in row["search_display"].lower()
        )
        print(
            f"X3   person 21009 Tjaerd Aylva: "
            f"{'found' if row else 'missing'} {'PASS' if x3_ok else 'FAIL'}"
        )
        if not x3_ok:
            failures.append("X3: pilot person 21009 missing or wrong")

        # X4: en/of — persons with BOTH functie+instelling ≤ persons with EITHER
        both = _scalar(
            conn,
            f"""
            SELECT COUNT(DISTINCT p.id) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND EXISTS (
                SELECT 1 FROM raa.aanstelling a
                WHERE a.persoon_id = p.id AND {REPUBLIEK_A}
                  AND a.functie_id = 561 AND a.instelling_id = 171
              )
            """,
        )
        either = _scalar(
            conn,
            f"""
            SELECT COUNT(DISTINCT p.id) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND EXISTS (
                SELECT 1 FROM raa.aanstelling a
                WHERE a.persoon_id = p.id AND {REPUBLIEK_A}
                  AND (a.functie_id = 561 OR a.instelling_id = 171)
              )
            """,
        )
        x4_ok = both > 0 and either >= both
        print(f"X4   en/of both={both} either={either} {'PASS' if x4_ok else 'FAIL'}")
        if not x4_ok:
            failures.append("X4: en/of counts inconsistent")

        # X5: shadow life dates expand P2 vs recorded-only
        with_shadow = _scalar(
            conn,
            f"""
            SELECT COUNT(*) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND COALESCE(p.geboorte_year, p.life_start_year) IS NOT NULL
              AND COALESCE(p.geboorte_year, p.life_start_year) >= 1700
              AND COALESCE(p.geboorte_year, p.life_start_year) <= 1750
            """,
        )
        exact = _scalar(
            conn,
            f"""
            SELECT COUNT(*) FROM raa.persoon p
            WHERE {REPUBLIEK_WHERE}
              AND p.geboorte_year IS NOT NULL
              AND p.geboorte_year >= 1700 AND p.geboorte_year <= 1750
            """,
        )
        x5_ok = with_shadow >= exact and with_shadow > exact
        print(
            f"X5   EDTF P2 shadow={with_shadow} exact={exact} "
            f"{'PASS' if x5_ok else 'FAIL'}"
        )
        if not x5_ok:
            failures.append("X5: shadow dates did not expand geboorte interval count")

    if args.do_assert and failures:
        print()
        print("ASSERT FAILED:", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        sys.exit(1)

    if args.do_assert:
        print()
        print("ASSERT OK")


if __name__ == "__main__":
    main()
