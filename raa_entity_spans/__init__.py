"""Import-time entity span tables (functie × instelling attestation)."""

from raa_entity_spans.spans import (
    build_functie_attestation,
    build_functie_instelling_span,
    sanitize_aanstelling_years,
)

__all__ = [
    "build_functie_instelling_span",
    "build_functie_attestation",
    "sanitize_aanstelling_years",
]
