"""Display formatting ported from legacy Zope views (persoon.pt, views.py)."""

from __future__ import annotations

from typing import Any

from raa_search_display.names import format_persoon_listing_name, format_persoon_naam

__all__ = [
    "ENTITY_SPAN_CAVEAT_HTML",
    "entity_profile",
    "format_corpus_witness",
    "format_heerlijkheid",
    "format_opmerkingen_html",
    "format_persoon_life_summary",
    "format_persoon_listing_name",
    "format_persoon_naam",
]


def _s(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"none", "nan", ""} else text


def _is_truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes"}
    return bool(value)


def format_life_event(
    *,
    label_born: str,
    date_text: str | None,
    plaats: str | None,
    approximate: bool,
) -> str:
    parts = [label_born + ":"]
    if approximate and date_text:
        parts.append("ca.")
    parts.append(date_text or "-")
    if _s(plaats):
        parts.append(f"te {plaats.strip()}")
    return " ".join(parts)


def format_persoon_life_summary(person: dict) -> dict[str, str]:
    geboorte_label = "gedoopt" if _is_truthy(person.get("doopjaar")) else "geboren"
    return {
        "geboorte": format_life_event(
            label_born=geboorte_label,
            date_text=_s(person.get("geboortedatum_als_bekend")),
            plaats=_s(person.get("geboorteplaats")),
            approximate=_is_truthy(person.get("onbepaaldgeboortedatum")),
        ),
        "overlijden": format_life_event(
            label_born="overleden",
            date_text=_s(person.get("overlijdensdatum_als_bekend")),
            plaats=_s(person.get("overlijdensplaats")),
            approximate=_is_truthy(person.get("onbepaaldoverlijdensdatum")),
        ),
    }


def format_heerlijkheid(person: dict) -> str | None:
    text = _s(person.get("heerlijkheid"))
    if not text:
        return None
    return f"heer van {text}."


def format_opmerkingen_html(text: str | None) -> str | None:
    raw = _s(text)
    if not raw:
        return None
    return raw.replace("\r\n", "\n").replace("\n", "<br />\n")


ENTITY_SPAN_CAVEAT_HTML = (
    '<p class="span-caveat">Vroegste en laatste <strong>gedateerde aanstelling in het bestand</strong>. '
    "Dezelfde functienaam kan in meerdere instellingen voorkomen; onderbrekingen tussen contexten "
    "worden niet ingevuld. Zie de "
    '<a href="https://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/zoekhulp" '
    'target="_blank" rel="noopener">zoekhulp</a> en de institutionele toelichting per instelling.</p>'
)


def format_corpus_witness(
    year: int | None,
    instelling_naam: str | None,
    instelling_id: int | None,
) -> str:
    if year is None:
        return "onbekend"
    year_text = str(int(year))
    name = _s(instelling_naam)
    if name and instelling_id:
        return (
            f'{year_text} — <a href="/static/instellingen.html?instelling={instelling_id}">'
            f"{name}</a>"
        )
    return year_text


def entity_profile(
    *,
    entity_type: str,
    entity_id: int,
    naam: str,
    stats: list[dict[str, str | int]],
    actions: list[dict[str, str]] | None = None,
    related: list[dict] | None = None,
    sections: list[dict[str, str]] | None = None,
) -> dict:
    return {
        "entity_type": entity_type,
        "id": entity_id,
        "naam": naam,
        "stats": stats,
        "actions": actions or [],
        "related": related or [],
        "sections": sections or [],
    }
