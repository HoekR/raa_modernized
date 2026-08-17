"""Merge raa_staging → raa with editorial conflict detection (E0)."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from raa_api.editorial_fields import EDITABLE_FIELDS, ENTITY_TABLE

STAGING_SCHEMA = "raa_staging"
RAA_SCHEMA = "raa"

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
    "functie_instelling_span",
    "functie_attestation",
]


def _norm(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text_val = str(value).strip()
    return text_val if text_val else None


def _cell(conn, schema: str, table: str, field: str, entity_id: int) -> str | None:
    row = conn.execute(
        text(f"SELECT {field} FROM {schema}.{table} WHERE id = :id"),
        {"id": entity_id},
    ).mappings().first()
    if not row:
        return None
    return _norm(row.get(field))


def detect_merge_conflicts(conn, release_id: str) -> list[dict[str, Any]]:
    """Compare active amendments against staging import; return conflict rows to insert."""
    conflicts: list[dict[str, Any]] = []
    amendments = conn.execute(
        text(
            """
            SELECT id, entity_type, entity_id, field, value
            FROM editorial.amendments
            WHERE status = 'active'
            """
        )
    ).mappings().all()

    for amend in amendments:
        entity_type = amend["entity_type"]
        field = amend["field"]
        if entity_type not in EDITABLE_FIELDS or field not in EDITABLE_FIELDS[entity_type]:
            continue
        table = ENTITY_TABLE.get(entity_type)
        if not table:
            continue
        old_base = _cell(conn, RAA_SCHEMA, table, field, int(amend["entity_id"]))
        new_base = _cell(conn, STAGING_SCHEMA, table, field, int(amend["entity_id"]))
        if old_base == new_base:
            continue
        amend_value = _norm(amend["value"])
        if amend_value == new_base:
            conn.execute(
                text(
                    """
                    UPDATE editorial.amendments
                    SET status = 'superseded', updated_at = NOW()
                    WHERE id = :id
                    """
                ),
                {"id": amend["id"]},
            )
            continue
        conflicts.append(
            {
                "amendment_id": int(amend["id"]),
                "entity_type": entity_type,
                "entity_id": int(amend["entity_id"]),
                "field": field,
                "old_base_value": old_base,
                "new_base_value": new_base,
                "amendment_value": amend_value,
                "release_id": release_id,
            }
        )
    return conflicts


def insert_conflicts(conn, conflicts: list[dict[str, Any]]) -> int:
    count = 0
    for row in conflicts:
        conn.execute(
            text(
                """
                INSERT INTO editorial.conflicts (
                    amendment_id, entity_type, entity_id, field,
                    old_base_value, new_base_value, amendment_value, release_id
                )
                VALUES (
                    :amendment_id, :entity_type, :entity_id, :field,
                    :old_base_value, :new_base_value, :amendment_value, :release_id
                )
                """
            ),
            row,
        )
        count += 1
    return count


def copy_staging_to_raa(conn, tables: list[str]) -> None:
    for table in tables:
        if table not in TABLE_ORDER:
            continue
        exists = conn.execute(
            text(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = :table
                """
            ),
            {"schema": STAGING_SCHEMA, "table": table},
        ).first()
        if not exists:
            continue
        conn.execute(text(f"DELETE FROM {RAA_SCHEMA}.{table}"))
        conn.execute(
            text(f"INSERT INTO {RAA_SCHEMA}.{table} SELECT * FROM {STAGING_SCHEMA}.{table}")
        )


def rebuild_span_tables(conn) -> None:
    """Rebuild derived span tables from merged aanstelling."""
    from raa_entity_spans.spans import build_functie_attestation, build_functie_instelling_span

    aanst = pd.read_sql(text("SELECT * FROM raa.aanstelling"), conn)
    inst = pd.read_sql(text("SELECT * FROM raa.instelling"), conn)
    span = build_functie_instelling_span(aanst, inst)
    attestation = build_functie_attestation(span, aanst, inst)
    span["import_release_id"] = conn.execute(
        text("SELECT import_release_id FROM raa.aanstelling LIMIT 1")
    ).scalar()
    attestation["import_release_id"] = span["import_release_id"].iloc[0] if len(span) else None
    conn.execute(text("DELETE FROM raa.functie_instelling_span"))
    conn.execute(text("DELETE FROM raa.functie_attestation"))
    if not span.empty:
        span.to_sql(
            "functie_instelling_span",
            conn,
            schema=RAA_SCHEMA,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500,
        )
    if not attestation.empty:
        attestation.to_sql(
            "functie_attestation",
            conn,
            schema=RAA_SCHEMA,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500,
        )


def merge_release_into_raa(engine: Engine, release_id: str) -> dict[str, int]:
    from raa_api.db import SessionLocal
    from raa_api.editorial import ensure_editorial_schema

    db = SessionLocal()
    try:
        ensure_editorial_schema(db)
    finally:
        db.close()

    stats = {"conflicts": 0, "tables": 0}
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS editorial"))
        conflicts = detect_merge_conflicts(conn, release_id)
        stats["conflicts"] = insert_conflicts(conn, conflicts)
        copy_staging_to_raa(conn, TABLE_ORDER)
        stats["tables"] = len(TABLE_ORDER)
        rebuild_span_tables(conn)
    return stats
