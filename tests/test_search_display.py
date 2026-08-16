from __future__ import annotations

import pandas as pd

from raa_search_display.names import format_persoon_naam
from raa_search_display.shadow import build_search_display, enrich_persoon_search_display


def test_build_search_display_includes_legacy_identity_fields():
    person = {
        "voornaam": "Tjaerd",
        "tussenvoegsel": "van",
        "geslachtsnaam": "Aylva",
        "searchable": "van Aylva",
        "heerlijkheid": "Waardenburg",
        "opmerkingen": "zich noemende baron",
    }
    blob = build_search_display(person)
    assert "Tjaerd van Aylva" in blob
    assert "baron" in blob
    assert "Waardenburg" in blob


def test_build_search_display_includes_titles_and_aliases():
    person = {
        "voornaam": "Willem Frederik",
        "geslachtsnaam": "Röell",
        "adellijke_titel": "baron",
        "academische_titel": "mr.dr.",
        "searchable": "Röell",
    }
    blob = build_search_display(person, aliases=["W.F. Röell"])
    assert format_persoon_naam(person) in blob
    assert "W.F. Röell" in blob
    assert "baron" in blob


def test_enrich_persoon_search_display_adds_column():
    persoon = pd.DataFrame(
        [
            {
                "id": 1,
                "voornaam": "Tjaerd",
                "tussenvoegsel": "van",
                "geslachtsnaam": "Aylva",
                "searchable": "van Aylva",
                "adellijketitel_id": None,
                "academischetitel_id": None,
                "heerlijkheid": None,
                "opmerkingen": "baron",
            }
        ]
    )
    enriched = enrich_persoon_search_display(persoon)
    assert "search_display" in enriched.columns
    assert "baron" in enriched.loc[0, "search_display"]
    assert "Tjaerd van Aylva" in enriched.loc[0, "search_display"]
