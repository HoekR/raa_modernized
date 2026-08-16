from raa_api.display import (
    entity_profile,
    format_corpus_witness,
    format_heerlijkheid,
    format_opmerkingen_html,
    format_persoon_life_summary,
    format_persoon_listing_name,
    format_persoon_naam,
)


def test_format_persoon_naam_jonkheer():
    person = {
        "adellijke_titel": "jonkheer",
        "academische_titel": "dr.",
        "voornaam": "Tjaerd",
        "tussenvoegsel": "baron van",
        "geslachtsnaam": "Aylva",
    }
    assert format_persoon_naam(person) == "jonkheer dr. Tjaerd baron van Aylva"


def test_format_persoon_listing_name_without_geslachtsnaam():
    person = {"voornaam": "Jan", "tussenvoegsel": None, "geslachtsnaam": ""}
    assert format_persoon_listing_name(person) == "Jan"


def test_format_persoon_life_summary_doopjaar():
    person = {
        "doopjaar": "1",
        "geboortedatum_als_bekend": "1701",
        "geboorteplaats": "Leeuwarden",
        "onbepaaldgeboortedatum": "0",
        "overlijdensdatum_als_bekend": "1760",
        "overlijdensplaats": "Grouw",
        "onbepaaldoverlijdensdatum": "1",
    }
    summary = format_persoon_life_summary(person)
    assert summary["geboorte"] == "gedoopt: 1701 te Leeuwarden"
    assert summary["overlijden"] == "overleden: ca. 1760 te Grouw"


def test_format_heerlijkheid():
    assert format_heerlijkheid({"heerlijkheid": "Oldeboorn"}) == "heer van Oldeboorn."
    assert format_heerlijkheid({"heerlijkheid": ""}) is None


def test_format_opmerkingen_html():
    assert format_opmerkingen_html("line one\nline two") == "line one<br />\nline two"
    assert format_opmerkingen_html(None) is None


def test_format_corpus_witness_with_instelling():
    html = format_corpus_witness(1582, "Staten van Friesland", 100)
    assert "1582" in html
    assert "Staten van Friesland" in html
    assert "instelling=100" in html


def test_entity_profile_shape():
    profile = entity_profile(
        entity_type="functie",
        entity_id=12,
        naam="Gedeputeerde",
        stats=[{"label": "Aanstellingen", "value": 42}],
        actions=[{"label": "Zoek", "href": "/static/index.html?functie_id=12"}],
    )
    assert profile["entity_type"] == "functie"
    assert profile["stats"][0]["value"] == 42
    assert profile["actions"][0]["href"].endswith("12")
