"""Batch fetch/save for spreadsheet-style editorial editing."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from raa_api.editorial import (
    get_active_amendment,
    revert_amendment,
    upsert_amendment,
)
from raa_api.editorial_enrich import refresh_persoon_derived
from raa_api.editorial_fields import (
    ENTITY_TABLE,
    GRID_COLUMN_GROUPS,
    GRID_FIELD_LABELS,
    assert_editable,
    field_spec,
    grid_fields,
)
from raa_api.editorial_dates import ALL_DATE_PART_FIELDS, validate_persoon_date_values


def _cell_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _field_state(
    db: Session,
    entity_type: str,
    entity_id: int,
    field: str,
    base_value: Any,
) -> dict[str, Any]:
    amendment = get_active_amendment(db, entity_type, entity_id, field)
    base = _cell_str(base_value)
    effective = _cell_str(amendment["value"]) if amendment else base
    return {
        "base": base,
        "effective": effective,
        "amended": amendment is not None,
        "amendment_id": amendment["id"] if amendment else None,
    }


def fetch_batch_rows(
    db: Session,
    entity_type: str,
    entity_ids: list[int],
    *,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    table = ENTITY_TABLE.get(entity_type)
    if not table:
        raise ValueError(f"Unknown entity type: {entity_type}")

    allowed = grid_fields(entity_type)
    if not allowed:
        raise ValueError(f"No grid fields for entity type: {entity_type}")

    if fields:
        unknown = [f for f in fields if f not in allowed]
        if unknown:
            raise ValueError(f"Fields not allowed in grid: {', '.join(unknown)}")
        use_fields = tuple(fields)
    else:
        use_fields = allowed

    rows: list[dict[str, Any]] = []
    found: set[int] = set()
    for entity_id in entity_ids:
        base_row = db.execute(
            text(f"SELECT * FROM raa.{table} WHERE id = :id"),
            {"id": entity_id},
        ).mappings().first()
        if not base_row:
            continue
        found.add(entity_id)
        base = dict(base_row)
        label = base.get("search_display") or base.get("geslachtsnaam") or str(entity_id)
        field_map = {
            name: _field_state(db, entity_type, entity_id, name, base.get(name))
            for name in use_fields
        }
        rows.append({"id": entity_id, "label": label, "fields": field_map})

    missing = [eid for eid in entity_ids if eid not in found]
    groups = GRID_COLUMN_GROUPS.get(entity_type, ())
    return {
        "entity_type": entity_type,
        "fields": list(use_fields),
        "rows": rows,
        "missing_ids": missing,
        "column_groups": [
            {"label": label, "fields": list(fields)} for label, fields in groups
        ],
        "field_labels": dict(GRID_FIELD_LABELS),
    }


def apply_batch_changes(
    db: Session,
    *,
    changes: list[dict[str, Any]],
    editor_id: str,
    note: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    applied: list[dict[str, Any]] = []
    reverted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    persoon_refresh: set[int] = set()

    for item in changes:
        entity_type = item["entity_type"]
        entity_id = int(item["entity_id"])
        field = item["field"]
        new_value = _cell_str(item.get("value"))

        try:
            assert_editable(entity_type, field)
        except ValueError as exc:
            errors.append(
                {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "field": field,
                    "error": str(exc),
                }
            )
            continue

        table = ENTITY_TABLE.get(entity_type)
        if not table:
            errors.append(
                {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "field": field,
                    "error": f"Unknown entity type: {entity_type}",
                }
            )
            continue

        base_row = db.execute(
            text(f"SELECT * FROM raa.{table} WHERE id = :id"),
            {"id": entity_id},
        ).mappings().first()
        if not base_row:
            errors.append(
                {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "field": field,
                    "error": "Entity not found",
                }
            )
            continue

        base = dict(base_row)
        amendment = get_active_amendment(db, entity_type, entity_id, field)
        base_val = _cell_str(base.get(field))
        effective = _cell_str(amendment["value"]) if amendment else base_val
        spec = field_spec(entity_type, field)
        entry = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "field": field,
        }

        if new_value == effective:
            skipped.append(entry)
            continue

        if new_value == base_val:
            if amendment:
                reverted_row = revert_amendment(db, int(amendment["id"]), commit=False)
                if reverted_row:
                    reverted.append(entry)
                    if spec and spec.triggers_persoon_enrich and entity_type == "persoon":
                        persoon_refresh.add(entity_id)
            else:
                skipped.append(entry)
            continue

        try:
            upsert_amendment(
                db,
                entity_type=entity_type,
                entity_id=entity_id,
                field=field,
                value=new_value,
                editor_id=editor_id,
                note=note,
                base_release_id=base.get("import_release_id"),
                commit=False,
            )
            applied.append(entry)
            if spec and spec.triggers_persoon_enrich and entity_type == "persoon":
                persoon_refresh.add(entity_id)
        except ValueError as exc:
            errors.append({**entry, "error": str(exc)})

    date_validation_errors: list[dict[str, Any]] = []
    if persoon_refresh:
        from raa_api.editorial_enrich import _effective_persoon_dict

        for persoon_id in sorted(persoon_refresh):
            person = _effective_persoon_dict(db, persoon_id)
            if not person:
                continue
            try:
                validate_persoon_date_values(person)
            except ValueError as exc:
                date_validation_errors.append(
                    {
                        "entity_type": "persoon",
                        "entity_id": persoon_id,
                        "field": "datum",
                        "error": str(exc),
                    }
                )

    if date_validation_errors:
        db.rollback()
        return {
            "applied": [],
            "reverted": [],
            "skipped": skipped,
            "errors": date_validation_errors + errors,
        }

    for persoon_id in persoon_refresh:
        refresh_persoon_derived(db, persoon_id, commit=False)

    if dry_run:
        db.rollback()
    else:
        db.commit()
    return {
        "applied": applied,
        "reverted": reverted,
        "skipped": skipped,
        "errors": errors,
        "dry_run": dry_run,
    }
