"""Person name formatting shared by import enrichment and the web API."""

from __future__ import annotations

from typing import Any


def _s(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"none", "nan", ""} else text


def format_persoon_naam(person: dict) -> str:
    """Full display name with titles (legacy Persoon.naam)."""
    adelspredikaat = ""
    adellijketitel = _s(person.get("adellijke_titel") or person.get("adellijketitel"))
    if adellijketitel.lower() == "jonkheer":
        adellijketitel = ""
        adelspredikaat = "jonkheer"
    parts = [
        adelspredikaat,
        _s(person.get("academische_titel") or person.get("academischetitel")),
        _s(person.get("voornaam")),
        adellijketitel,
        _s(person.get("tussenvoegsel")),
        _s(person.get("geslachtsnaam")),
    ]
    return " ".join(p for p in parts if p)


def format_persoon_listing_name(person: dict) -> str:
    """Listing label without awkward leading comma when geslachtsnaam is empty."""
    gs = _s(person.get("geslachtsnaam"))
    vn = _s(person.get("voornaam"))
    tv = _s(person.get("tussenvoegsel"))
    if gs:
        return " ".join(p for p in [vn, tv, gs] if p)
    return vn or format_persoon_naam(person)


def normalize_search_text(value: Any) -> str:
    text = _s(value)
    return " ".join(text.split())
