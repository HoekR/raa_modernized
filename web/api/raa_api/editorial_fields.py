"""Editable field registry for editorial amendments (Milestone E)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SanitizeMode = Literal["html", "text", "life_year", "life_month", "life_day"]


@dataclass(frozen=True)
class FieldSpec:
    sanitize: SanitizeMode
    searchable: bool = False
    triggers_persoon_enrich: bool = False


ENTITY_TABLE: dict[str, str] = {
    "instelling": "instelling",
    "persoon": "persoon",
    "aanstelling": "aanstelling",
}

EDITABLE_FIELDS: dict[str, dict[str, FieldSpec]] = {
    "instelling": {
        "toelichting": FieldSpec(sanitize="html"),
    },
    "persoon": {
        "opmerkingen": FieldSpec(sanitize="text", searchable=True, triggers_persoon_enrich=True),
        "geslachtsnaam": FieldSpec(sanitize="text", searchable=True, triggers_persoon_enrich=True),
        "voornaam": FieldSpec(sanitize="text", searchable=True, triggers_persoon_enrich=True),
        "tussenvoegsel": FieldSpec(sanitize="text", searchable=True, triggers_persoon_enrich=True),
        "heerlijkheid": FieldSpec(sanitize="text", searchable=True, triggers_persoon_enrich=True),
        "geboortejaar": FieldSpec(sanitize="life_year", triggers_persoon_enrich=True),
        "geboortemaand": FieldSpec(sanitize="life_month", triggers_persoon_enrich=True),
        "geboortedag": FieldSpec(sanitize="life_day", triggers_persoon_enrich=True),
        "overlijdensjaar": FieldSpec(sanitize="life_year", triggers_persoon_enrich=True),
        "overlijdensmaand": FieldSpec(sanitize="life_month", triggers_persoon_enrich=True),
        "overlijdensdag": FieldSpec(sanitize="life_day", triggers_persoon_enrich=True),
    },
    "aanstelling": {
        "opmerkingen": FieldSpec(sanitize="text", searchable=True),
    },
}


def field_spec(entity_type: str, field: str) -> FieldSpec | None:
    return EDITABLE_FIELDS.get(entity_type, {}).get(field)


def assert_editable(entity_type: str, field: str) -> FieldSpec:
    spec = field_spec(entity_type, field)
    if spec is None:
        raise ValueError(f"Field not editable: {entity_type}.{field}")
    return spec


# Spreadsheet columns: exact dates as y / m / d (m and d optional).
GRID_FIELDS: dict[str, tuple[str, ...]] = {
    "persoon": (
        "geslachtsnaam",
        "voornaam",
        "tussenvoegsel",
        "geboortejaar",
        "geboortemaand",
        "geboortedag",
        "overlijdensjaar",
        "overlijdensmaand",
        "overlijdensdag",
        "opmerkingen",
    ),
}

GRID_COLUMN_GROUPS: dict[str, tuple[tuple[str | None, tuple[str, ...]], ...]] = {
    "persoon": (
        (None, ("geslachtsnaam", "voornaam", "tussenvoegsel")),
        ("geboorte", ("geboortejaar", "geboortemaand", "geboortedag")),
        ("overlijden", ("overlijdensjaar", "overlijdensmaand", "overlijdensdag")),
        (None, ("opmerkingen",)),
    ),
}

GRID_FIELD_LABELS: dict[str, str] = {
    "geboortejaar": "j",
    "geboortemaand": "m",
    "geboortedag": "d",
    "overlijdensjaar": "j",
    "overlijdensmaand": "m",
    "overlijdensdag": "d",
}


def grid_fields(entity_type: str) -> tuple[str, ...]:
    return GRID_FIELDS.get(entity_type, ())
