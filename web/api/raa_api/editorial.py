"""Editorial amendment overlay — survives re-import (schema editorial.*)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import nh3
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from raa_api.editorial_fields import ENTITY_TABLE, assert_editable, field_spec
from raa_life_dates.validate import is_plausible_life_year

from raa_api.editorial_dates import (
    ALL_DATE_PART_FIELDS,
    sanitize_life_day,
    sanitize_life_month,
    validate_persoon_date_values,
)

_EDITORIAL_SCHEMA = """
CREATE SCHEMA IF NOT EXISTS editorial;

CREATE TABLE IF NOT EXISTS editorial.amendments (
    id SERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    field TEXT NOT NULL,
    value TEXT,
    base_release_id TEXT,
    editor_id TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_amendments_active_unique
    ON editorial.amendments (entity_type, entity_id, field)
    WHERE status = 'active';

CREATE TABLE IF NOT EXISTS editorial.conflicts (
    id SERIAL PRIMARY KEY,
    amendment_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    field TEXT NOT NULL,
    old_base_value TEXT,
    new_base_value TEXT,
    amendment_value TEXT,
    release_id TEXT NOT NULL,
    resolution TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

_ALLOWED_HTML_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "ul",
    "ol",
    "li",
    "a",
    "h2",
    "h3",
    "h4",
    "blockquote",
}


def ensure_editorial_schema(db: Session) -> None:
    for statement in _EDITORIAL_SCHEMA.strip().split(";"):
        chunk = statement.strip()
        if chunk:
            db.execute(text(chunk))
    db.commit()


def sanitize_html(value: str | None) -> str:
    if not value:
        return ""
    return nh3.clean(value.strip(), tags=_ALLOWED_HTML_TAGS)


def sanitize_text(value: str | None) -> str:
    if not value:
        return ""
    return value.strip()


def sanitize_field_value(entity_type: str, field: str, value: str) -> str:
    spec = assert_editable(entity_type, field)
    if spec.sanitize == "html":
        return sanitize_html(value)
    if spec.sanitize == "life_year":
        text_val = sanitize_text(value)
        if not text_val:
            return ""
        try:
            year = int(float(text_val.replace(".0", "")))
        except ValueError as exc:
            raise ValueError(f"Invalid year for {field}: {value!r}") from exc
        if not is_plausible_life_year(year):
            raise ValueError(f"Year out of range for {field}: {year}")
        return str(year)
    if spec.sanitize == "life_month":
        return sanitize_life_month(value, field=field)
    if spec.sanitize == "life_day":
        return sanitize_life_day(value, field=field)
    return sanitize_text(value)


def effective_column_sql(entity_type: str, field: str, table_alias: str, column: str) -> str:
    """SQL expression: COALESCE(active amendment, base column)."""
    return f"""COALESCE(
        (SELECT a.value FROM editorial.amendments a
         WHERE a.entity_type = '{entity_type}'
           AND a.entity_id = {table_alias}.id
           AND a.field = '{field}'
           AND a.status = 'active'),
        {table_alias}.{column}
    )"""


def get_active_amendment(
    db: Session,
    entity_type: str,
    entity_id: int,
    field: str,
) -> dict[str, Any] | None:
    try:
        row = db.execute(
            text(
                """
                SELECT id, entity_type, entity_id, field, value, base_release_id,
                       editor_id, note, status, created_at, updated_at
                FROM editorial.amendments
                WHERE entity_type = :entity_type
                  AND entity_id = :entity_id
                  AND field = :field
                  AND status = 'active'
                """
            ),
            {"entity_type": entity_type, "entity_id": entity_id, "field": field},
        ).mappings().first()
    except ProgrammingError:
        db.rollback()
        return None
    return dict(row) if row else None


def apply_effective_value(
    db: Session,
    entity_type: str,
    entity_id: int,
    field: str,
    base_value: str | None,
) -> tuple[str | None, bool]:
    """Return (effective_value, is_amended)."""
    amendment = get_active_amendment(db, entity_type, entity_id, field)
    if amendment is None:
        return base_value, False
    return amendment.get("value"), True


def list_amendments(
    db: Session,
    *,
    entity_type: str | None = None,
    entity_id: int | None = None,
    status: str = "active",
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses = ["status = :status"]
    params: dict[str, Any] = {"status": status, "limit": limit}
    if entity_type:
        clauses.append("entity_type = :entity_type")
        params["entity_type"] = entity_type
    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = entity_id
    where = " AND ".join(clauses)
    rows = db.execute(
        text(
            f"""
            SELECT id, entity_type, entity_id, field, value, base_release_id,
                   editor_id, note, status, created_at, updated_at
            FROM editorial.amendments
            WHERE {where}
            ORDER BY updated_at DESC
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


def upsert_amendment(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    field: str,
    value: str,
    editor_id: str,
    note: str | None = None,
    base_release_id: str | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    ensure_editorial_schema(db)
    clean_value = sanitize_field_value(entity_type, field, value)
    now = datetime.now(timezone.utc)
    db.execute(
        text(
            """
            UPDATE editorial.amendments
            SET status = 'superseded', updated_at = :now
            WHERE entity_type = :entity_type
              AND entity_id = :entity_id
              AND field = :field
              AND status = 'active'
            """
        ),
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field": field,
            "now": now,
        },
    )
    row = db.execute(
        text(
            """
            INSERT INTO editorial.amendments (
                entity_type, entity_id, field, value, base_release_id,
                editor_id, note, status, created_at, updated_at
            )
            VALUES (
                :entity_type, :entity_id, :field, :value, :base_release_id,
                :editor_id, :note, 'active', :now, :now
            )
            RETURNING id, entity_type, entity_id, field, value, base_release_id,
                      editor_id, note, status, created_at, updated_at
            """
        ),
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field": field,
            "value": clean_value,
            "base_release_id": base_release_id,
            "editor_id": editor_id,
            "note": note,
            "now": now,
        },
    ).mappings().first()
    if commit:
        db.commit()
    return dict(row)


def revert_amendment(db: Session, amendment_id: int, *, commit: bool = True) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            UPDATE editorial.amendments
            SET status = 'reverted', updated_at = NOW()
            WHERE id = :id AND status = 'active'
            RETURNING id, entity_type, entity_id, field, status
            """
        ),
        {"id": amendment_id},
    ).mappings().first()
    if not row:
        return None
    result = dict(row)
    spec = field_spec(result["entity_type"], result["field"])
    if result["entity_type"] == "persoon" and result["field"] in ALL_DATE_PART_FIELDS:
        from raa_api.editorial_enrich import _effective_persoon_dict

        person = _effective_persoon_dict(db, int(result["entity_id"]))
        if person:
            validate_persoon_date_values(person)
    if commit and spec and spec.triggers_persoon_enrich and result["entity_type"] == "persoon":
        from raa_api.editorial_enrich import refresh_persoon_derived

        refresh_persoon_derived(db, int(result["entity_id"]))
    elif commit:
        db.commit()
    return result


def upsert_amendment_with_side_effects(
    db: Session,
    *,
    entity_type: str,
    entity_id: int,
    field: str,
    value: str,
    editor_id: str,
    note: str | None = None,
    base_release_id: str | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    row = upsert_amendment(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        field=field,
        value=value,
        editor_id=editor_id,
        note=note,
        base_release_id=base_release_id,
        commit=False,
    )
    if entity_type == "persoon" and field in ALL_DATE_PART_FIELDS:
        from raa_api.editorial_enrich import _effective_persoon_dict

        person = _effective_persoon_dict(db, entity_id)
        if person:
            validate_persoon_date_values(person)
    spec = field_spec(entity_type, field)
    if spec and spec.triggers_persoon_enrich and entity_type == "persoon":
        if commit:
            from raa_api.editorial_enrich import refresh_persoon_derived

            refresh_persoon_derived(db, entity_id)
        else:
            return row
    if commit:
        db.commit()
    return row


def list_conflicts(db: Session, *, unresolved_only: bool = True, limit: int = 100) -> list[dict[str, Any]]:
    clause = "resolution IS NULL" if unresolved_only else "TRUE"
    rows = db.execute(
        text(
            f"""
            SELECT id, amendment_id, entity_type, entity_id, field,
                   old_base_value, new_base_value, amendment_value, release_id,
                   resolution, resolved_at, created_at
            FROM editorial.conflicts
            WHERE {clause}
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


def resolve_conflict(db: Session, conflict_id: int, resolution: str) -> dict[str, Any] | None:
    if resolution not in {"keep_amendment", "accept_base"}:
        raise ValueError("resolution must be keep_amendment or accept_base")
    row = db.execute(
        text("SELECT * FROM editorial.conflicts WHERE id = :id AND resolution IS NULL"),
        {"id": conflict_id},
    ).mappings().first()
    if not row:
        return None
    conflict = dict(row)
    if resolution == "accept_base":
        db.execute(
            text(
                """
                UPDATE editorial.amendments
                SET status = 'reverted', updated_at = NOW()
                WHERE id = :id AND status = 'active'
                """
            ),
            {"id": conflict["amendment_id"]},
        )
        spec = field_spec(conflict["entity_type"], conflict["field"])
        if spec and spec.triggers_persoon_enrich and conflict["entity_type"] == "persoon":
            from raa_api.editorial_enrich import refresh_persoon_derived

            refresh_persoon_derived(db, int(conflict["entity_id"]))
    db.execute(
        text(
            """
            UPDATE editorial.conflicts
            SET resolution = :resolution, resolved_at = NOW()
            WHERE id = :id
            """
        ),
        {"id": conflict_id, "resolution": resolution},
    )
    db.commit()
    return conflict


def entity_exists(db: Session, entity_type: str, entity_id: int) -> bool:
    table = ENTITY_TABLE.get(entity_type)
    if not table:
        return False
    return (
        db.execute(
            text(f"SELECT 1 FROM raa.{table} WHERE id = :id"),
            {"id": entity_id},
        ).first()
        is not None
    )


def get_entity_edit_context(db: Session, entity_type: str, entity_id: int) -> dict[str, Any] | None:
    from raa_api.editorial_fields import EDITABLE_FIELDS

    table = ENTITY_TABLE.get(entity_type)
    if not table or entity_type not in EDITABLE_FIELDS:
        return None
    base_row = db.execute(
        text(f"SELECT * FROM raa.{table} WHERE id = :id"),
        {"id": entity_id},
    ).mappings().first()
    if not base_row:
        return None
    base = dict(base_row)
    fields: dict[str, dict[str, Any]] = {}
    for name in EDITABLE_FIELDS[entity_type]:
        amendment = get_active_amendment(db, entity_type, entity_id, name)
        base_val = base.get(name)
        effective = amendment["value"] if amendment else base_val
        fields[name] = {
            "base": base_val,
            "effective": effective,
            "amended": amendment is not None,
            "amendment_id": amendment["id"] if amendment else None,
        }
    label = base.get("naam") or base.get("geslachtsnaam") or str(entity_id)
    return {
        "entity_type": entity_type,
        "id": entity_id,
        "label": label,
        "fields": fields,
        "import_release_id": base.get("import_release_id"),
    }


def get_instelling_toelichting_edit_context(db: Session, instelling_id: int) -> dict[str, Any] | None:
    base_row = db.execute(
        text("SELECT id, naam, toelichting, import_release_id FROM raa.instelling WHERE id = :id"),
        {"id": instelling_id},
    ).mappings().first()
    if not base_row:
        return None
    base = dict(base_row)
    amendment = get_active_amendment(db, "instelling", instelling_id, "toelichting")
    effective = amendment["value"] if amendment else base.get("toelichting")
    history = list_amendments(
        db, entity_type="instelling", entity_id=instelling_id, status="active", limit=1
    )
    all_history = db.execute(
        text(
            """
            SELECT id, editor_id, note, status, created_at, updated_at
            FROM editorial.amendments
            WHERE entity_type = 'instelling' AND entity_id = :id AND field = 'toelichting'
            ORDER BY updated_at DESC
            LIMIT 20
            """
        ),
        {"id": instelling_id},
    ).mappings().all()
    return {
        "id": base["id"],
        "naam": base["naam"],
        "toelichting_base": base.get("toelichting"),
        "toelichting_effective": effective,
        "toelichting_amended": amendment is not None,
        "amendment": amendment,
        "base_release_id": base.get("import_release_id"),
        "history": [dict(r) for r in all_history],
        "active_amendment": history[0] if history else None,
    }
