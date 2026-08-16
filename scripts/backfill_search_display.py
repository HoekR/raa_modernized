#!/usr/bin/env python3
"""Backfill persoon.search_display on an existing PostgreSQL import."""

from __future__ import annotations

import os

import pandas as pd
from sqlalchemy import create_engine, text

from raa_search_display.shadow import enrich_persoon_search_display


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )


def main() -> None:
    engine = create_engine(database_url())
    with engine.begin() as conn:
        persoon = pd.read_sql(text("SELECT * FROM raa.persoon"), conn)
        alias = pd.read_sql(text("SELECT * FROM raa.alias"), conn)
        adellijke_titel = pd.read_sql(text("SELECT * FROM raa.adellijke_titel"), conn)
        academische_titel = pd.read_sql(text("SELECT * FROM raa.academische_titel"), conn)

    enriched = enrich_persoon_search_display(persoon, alias, adellijke_titel, academische_titel)
    updates = enriched[["id", "search_display"]]

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE raa.persoon ADD COLUMN IF NOT EXISTS search_display TEXT"))
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_persoon_search_display ON raa.persoon (search_display)")
        )
        chunk_size = 500
        records = updates.to_dict("records")
        for start in range(0, len(records), chunk_size):
            chunk = records[start : start + chunk_size]
            conn.execute(
                text(
                    """
                    UPDATE raa.persoon AS p
                    SET search_display = v.search_display
                    FROM (
                        SELECT unnest(CAST(:ids AS int[])) AS id,
                               unnest(CAST(:displays AS text[])) AS search_display
                    ) AS v
                    WHERE p.id = v.id
                    """
                ),
                {
                    "ids": [int(row["id"]) for row in chunk],
                    "displays": [row["search_display"] for row in chunk],
                },
            )

    sample = updates.loc[updates["id"] == 21009, "search_display"]
    print(f"Backfilled search_display for {len(updates)} persons")
    if not sample.empty:
        print(f"21009: {sample.iloc[0][:120]}...")


if __name__ == "__main__":
    main()
