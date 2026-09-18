"""Person name formatting shared by import enrichment and the web API."""

from __future__ import annotations

from typing import Any

LISTING_NAME_MAX = 72


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


def format_persoon_listing_name(person: dict, *, max_len: int = LISTING_NAME_MAX) -> str:
    """Surname-first listing label with titles; truncate long voornaam first.

    Format: ``Geslachtsnaam, [acad] [jonkheer?] voornaam [adel] [tussenvoegsel]``
    """
    gs = _s(person.get("geslachtsnaam"))
    vn = _s(person.get("voornaam"))
    tv = _s(person.get("tussenvoegsel"))
    acad = _s(person.get("academische_titel") or person.get("academischetitel"))
    adel = _s(person.get("adellijke_titel") or person.get("adellijketitel"))
    pred = ""
    if adel.lower() == "jonkheer":
        adel = ""
        pred = "jonkheer"

    if not gs:
        return vn or format_persoon_naam(person)

    def build(voornaam: str) -> str:
        rest = " ".join(p for p in [acad, pred, voornaam, adel, tv] if p)
        return f"{gs}, {rest}" if rest else gs

    full = build(vn)
    if len(full) <= max_len:
        return full

    # Prefer cutting voornaam before dropping the whole string.
    if vn:
        other = " ".join(p for p in [acad, pred, adel, tv] if p)
        other_len = len(other) + (1 if other and vn else 0)
        budget = max_len - len(gs) - 2 - other_len  # "gs, "
        if budget >= 8:
            truncated_vn = vn[: budget - 1].rstrip(" ,;") + "…"
            full = build(truncated_vn)
            if len(full) <= max_len:
                return full

    if len(full) <= max_len:
        return full
    return full[: max_len - 1].rstrip() + "…"


def normalize_search_text(value: Any) -> str:
    text = _s(value)
    return " ".join(text.split())
