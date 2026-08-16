"""Import-time shadow search blob for personen (legacy identity fields + display name)."""

from __future__ import annotations

import pandas as pd

from raa_search_display.names import format_persoon_naam, normalize_search_text


def build_search_display(person: dict, *, aliases: list[str] | None = None) -> str:
    """Concatenate legacy personen identity fields into one searchable string."""
    parts = [
        format_persoon_naam(person),
        normalize_search_text(person.get("searchable")),
        normalize_search_text(person.get("heerlijkheid")),
        normalize_search_text(person.get("opmerkingen")),
    ]
    if aliases:
        parts.extend(normalize_search_text(name) for name in aliases if name)
    return normalize_search_text(" ".join(p for p in parts if p))


def _title_lookup(frame: pd.DataFrame | None) -> dict[int, str]:
    if frame is None or frame.empty or "id" not in frame.columns or "naam" not in frame.columns:
        return {}
    return frame.set_index("id")["naam"].astype(str).to_dict()


def _alias_lookup(alias: pd.DataFrame | None) -> dict[int, list[str]]:
    if alias is None or alias.empty:
        return {}
    grouped = alias.groupby("persoon_id", dropna=True)["naam"]
    return {int(pid): [str(name) for name in names.dropna()] for pid, names in grouped}


def enrich_persoon_search_display(
    persoon: pd.DataFrame,
    alias: pd.DataFrame | None = None,
    adellijke_titel: pd.DataFrame | None = None,
    academische_titel: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add `search_display`: import-time shadow of legacy personen identity search."""
    result = persoon.copy()
    adt = _title_lookup(adellijke_titel)
    act = _title_lookup(academische_titel)
    alias_by_person = _alias_lookup(alias)

    displays: list[str] = []
    for person in result.to_dict("records"):
        adt_id = person.get("adellijketitel_id")
        act_id = person.get("academischetitel_id")
        if adt_id is not None and not (isinstance(adt_id, float) and pd.isna(adt_id)):
            person["adellijke_titel"] = adt.get(int(adt_id))
        if act_id is not None and not (isinstance(act_id, float) and pd.isna(act_id)):
            person["academische_titel"] = act.get(int(act_id))
        aliases = alias_by_person.get(int(person["id"]), [])
        displays.append(build_search_display(person, aliases=aliases))

    result["search_display"] = displays
    return result
