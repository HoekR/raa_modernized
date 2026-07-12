#!/usr/bin/env python3
"""Import extab.pkl release into PostgreSQL. Customize TABLE_ORDER in project if needed."""

from __future__ import annotations

import argparse
import os
import pickle
import subprocess
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PERIOD_COLUMNS = (
    "me",
    "republiek",
    "republiek_friezen",
    "batfra",
    "negentiende_eeuw",
)

OTHER_PERIOD_COLUMNS = PERIOD_COLUMNS

# Rows flagged divperioden are superseded by republiek_friezen data (see raa_convert CONVERSION_NOTES).
DROP_DIVPERIODEN_TABLES = frozenset({"persoon", "aanstelling", "alias", "bron_details"})

TABLE_ORDER = [
    "academische_titel",
    "adellijke_titel",
    "stand",
    "gewest",
    "provincie",
    "regio",
    "lokaal",
    "functie",
    "instelling",
    "bron",
    "persoon",
    "alias",
    "bron_details",
    "aanstelling",
]


def load_extab(path: Path) -> dict[str, pd.DataFrame]:
    with path.open("rb") as handle:
        data = pickle.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} does not contain an extab dict")
    return {k: v for k, v in data.items() if k}


def validate_export(path: Path) -> None:
    raa_convert = path.parent
    validator = raa_convert / "validate_export.py"
    if validator.exists():
        subprocess.run(
            [sys.executable, str(validator), "--pickle", str(path)],
            check=True,
            cwd=raa_convert,
        )


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )


def purge_divperioden(extab: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Drop divperioden rows superseded by republiek_friezen; strip div flag on shared lookups."""
    cleaned: dict[str, pd.DataFrame] = {}
    for name, frame in extab.items():
        if "divperioden" not in frame.columns:
            cleaned[name] = frame
            continue

        table = frame.copy()
        if name in DROP_DIVPERIODEN_TABLES:
            drop = table["divperioden"] == 1
            if "mark_for_delete" in table.columns:
                drop = drop | (table["mark_for_delete"] == 1)
            removed = int(drop.sum())
            if removed:
                print(f"  {name}: dropped {removed} divperioden rows")
            cleaned[name] = table.loc[~drop].copy()
            continue

        other_active = pd.Series(False, index=table.index)
        for col in OTHER_PERIOD_COLUMNS:
            if col in table.columns:
                other_active = other_active | (table[col] == 1)

        div_only = (table["divperioden"] == 1) & ~other_active
        removed = int(div_only.sum())
        if removed:
            print(f"  {name}: dropped {removed} divperioden-only rows")
        table = table.loc[~div_only].copy()
        stripped = int((table["divperioden"] == 1).sum())
        if stripped:
            table.loc[table["divperioden"] == 1, "divperioden"] = 0
            print(f"  {name}: cleared divperioden flag on {stripped} shared rows")
        cleaned[name] = table

    return cleaned


def import_tables(extab: dict[str, pd.DataFrame], engine, release_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raa"))
        for table in TABLE_ORDER:
            if table not in extab:
                continue
            frame = extab[table].copy()
            frame["import_release_id"] = release_id
            frame.to_sql(
                table,
                conn,
                schema="raa",
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=500,
            )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_persoon_searchable "
                "ON raa.persoon (searchable)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_persoon_geslachtsnaam "
                "ON raa.persoon (geslachtsnaam)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_aanstelling_persoon "
                "ON raa.aanstelling (persoon_id)"
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import extab.pkl into PostgreSQL")
    parser.add_argument(
        "--pickle",
        type=Path,
        default=None,
        help="Path to extab.pkl (default: load via data_io manifest)",
    )
    parser.add_argument("--release-id", default="dev")
    parser.add_argument("--skip-validate", action="store_true")
    args = parser.parse_args()

    if args.pickle:
        pickle_path = args.pickle
    else:
        from data_io import resolve

        pickle_path = Path(resolve("raa_extab"))

    if not args.skip_validate:
        validate_export(pickle_path)

    extab = load_extab(pickle_path)
    print("Purging divperioden rows superseded by republiek_friezen...")
    extab = purge_divperioden(extab)
    engine = create_engine(database_url())
    import_tables(extab, engine, args.release_id)
    print(f"Imported {len(TABLE_ORDER)} tables into {database_url()} (release {args.release_id})")


if __name__ == "__main__":
    main()
