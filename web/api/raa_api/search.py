from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from raa_api.config import PERIODS
from raa_api.display import (
    ENTITY_SPAN_CAVEAT_HTML,
    entity_profile,
    format_corpus_witness,
    format_heerlijkheid,
    format_opmerkingen_html,
    format_persoon_life_summary,
    format_persoon_listing_name,
    format_persoon_naam,
)
from raa_api.editorial import apply_effective_value, effective_column_sql
from raa_api.editorial_fields import EDITABLE_FIELDS
from raa_api.edtf_bounds import _year_column, life_year_overlap_sql
from raa_api.schemas import (
    FacetValue,
    PeriodCount,
    SearchRequest,
    SearchResponse,
    SummaryResponse,
    TimelineMeta,
    text_search_patterns,
)
from raa_api.timeline import (
    compress_stacked_timeline,
    compress_timeline,
    merge_period_year_rows,
)

# republiek_friezen: separately edited Fries rows in raa_convert — included when filtering Republiek.
PERIOD_FLAG_COLUMNS: dict[str, tuple[str, ...]] = {
    "republiek": ("republiek", "republiek_friezen"),
    "batfra": ("batfra",),
    "negentiende_eeuw": ("negentiende_eeuw",),
    "me": ("me",),
}


def _period_match_sql(prefix: str, period: str) -> str:
    flags = PERIOD_FLAG_COLUMNS.get(period)
    if not flags:
        return "TRUE"
    parts = [f"{prefix}.{col} = 1" for col in flags]
    if len(parts) == 1:
        return parts[0]
    return f"({' OR '.join(parts)})"


def _period_clause(prefix: str, period: str | None, mode: str) -> str:
    if mode == "overall" or not period or period == "all":
        return "TRUE"
    return _period_match_sql(prefix, period)


def _life_date_clauses(req: SearchRequest) -> tuple[list[str], dict]:
    clauses: list[str] = []
    params: dict = {}
    include_shadow = req.include_shadow_dates

    for i, value in enumerate(req.filters.get("geboorte", [])):
        if not value:
            continue
        sql, p = life_year_overlap_sql("geboorte", value, include_shadow=include_shadow, param_prefix=f"geb{i}")
        clauses.append(f"({sql})")
        params.update(p)

    for i, value in enumerate(req.filters.get("overlijden", [])):
        if not value:
            continue
        sql, p = life_year_overlap_sql("overlijden", value, include_shadow=include_shadow, param_prefix=f"ovl{i}")
        clauses.append(f"({sql})")
        params.update(p)

    return clauses, params


def _persoon_text_token_clause(param_key: str) -> str:
    """One query token must match search_display and/or legacy identity fields."""
    legacy_fields = f"""
        p.searchable ILIKE :{param_key}
        OR p.geslachtsnaam ILIKE :{param_key}
        OR p.voornaam ILIKE :{param_key}
        OR p.tussenvoegsel ILIKE :{param_key}
        OR p.heerlijkheid ILIKE :{param_key}
        OR {effective_column_sql("persoon", "opmerkingen", "p", "opmerkingen")} ILIKE :{param_key}
        OR EXISTS (
            SELECT 1 FROM raa.alias al
            WHERE al.persoon_id = p.id AND al.naam ILIKE :{param_key}
        )
        OR EXISTS (
            SELECT 1 FROM raa.adellijke_titel adt
            WHERE adt.id = p.adellijketitel_id AND adt.naam ILIKE :{param_key}
        )
        OR EXISTS (
            SELECT 1 FROM raa.academische_titel act
            WHERE act.id = p.academischetitel_id AND act.naam ILIKE :{param_key}
        )
    """
    return f"""(
        COALESCE(p.search_display, '') ILIKE :{param_key}
        OR ({legacy_fields.strip()})
    )"""


_PERSON_NAME_PART_COLUMNS: dict[str, str] = {
    "geslachtsnaam": "p.geslachtsnaam",
    "voornaam": "p.voornaam",
    "tussenvoegsel": "p.tussenvoegsel",
    "heerlijkheid": "p.heerlijkheid",
}


def _persoon_name_part_clauses(filters: dict[str, list[str]], params: dict) -> list[str]:
    """Structured name-field filters (AND across fields; wildcards per field)."""
    clauses: list[str] = []
    for field, column in _PERSON_NAME_PART_COLUMNS.items():
        value = (_date_filter(filters, field) or "").strip()
        if not value:
            continue
        for i, pattern in enumerate(text_search_patterns(value, anchor="prefix")):
            key = f"np_{field}_{i}"
            clauses.append(f"{column} ILIKE :{key}")
            params[key] = pattern
    alias = (_date_filter(filters, "alias") or "").strip()
    if alias:
        for i, pattern in enumerate(text_search_patterns(alias, anchor="prefix")):
            key = f"np_alias_{i}"
            clauses.append(
                "EXISTS (SELECT 1 FROM raa.alias al "
                f"WHERE al.persoon_id = p.id AND al.naam ILIKE :{key})"
            )
            params[key] = pattern
    return clauses


def _persoon_where(
    req: SearchRequest, *, omit_filter_keys: set[str] | None = None
) -> tuple[str, dict]:
    """Build personen WHERE. omit_filter_keys skips those filters (for disjunctive facets)."""
    omit = omit_filter_keys or set()
    where = [_period_clause("p", req.period, req.period_mode)]
    params: dict = {}

    if req.q:
        anchor = req.q_mode if req.q_mode in ("prefix", "contains", "pattern", "exact") else "prefix"
        patterns = text_search_patterns(req.q, anchor=anchor)
        for i, pattern in enumerate(patterns):
            key = f"q{i}"
            where.append(_persoon_text_token_clause(key))
            params[key] = pattern

    where.extend(_persoon_name_part_clauses(req.filters, params))

    if "instelling_id" not in omit:
        instelling_ids = _int_ids(req.filters, "instelling_id")
        if instelling_ids:
            where.extend(
                _multi_fk_clauses(
                    "p",
                    "instelling_id",
                    instelling_ids,
                    req.instelling_match,
                    req.period,
                    req.period_mode,
                )
            )

    if "functie_id" not in omit:
        functie_ids = _int_ids(req.filters, "functie_id")
        if functie_ids:
            where.extend(
                _multi_fk_clauses(
                    "p",
                    "functie_id",
                    functie_ids,
                    req.functie_match,
                    req.period,
                    req.period_mode,
                )
            )

    geo_filters = (
        {k: v for k, v in req.filters.items() if k not in omit}
        if omit
        else req.filters
    )
    where.extend(_geo_exists_clauses("p", geo_filters))
    if "stand_id" not in omit:
        where.extend(_stand_exists_clauses("p", req.filters))
    if "adel" not in omit:
        where.extend(_adel_person_clause(req.filters))
    letter = (_date_filter(req.filters, "letter") or "").strip().upper()
    if letter and letter != "ALL":
        name_letter = (
            "LEFT(UPPER(COALESCE(NULLIF(TRIM(p.geslachtsnaam), ''), "
            "NULLIF(TRIM(p.voornaam), ''), '')), 1)"
        )
        if letter == "#":
            where.append(f"({name_letter} = '' OR {name_letter} !~ '^[A-Z]$')")
        elif len(letter) == 1 and letter.isalpha():
            where.append(f"{name_letter} = :naam_letter")
            params["naam_letter"] = letter
    life_clauses, life_params = _life_date_clauses(req)
    where.extend(life_clauses)
    params.update(life_params)
    date_clauses, date_params = _persoon_aanstelling_date_clauses(req)
    where.extend(date_clauses)
    params.update(date_params)

    return " AND ".join(where), params


def _normalize_filter_date(value: str | None, *, end: bool = False) -> str | None:
    """Accept YYYY-MM-DD or year-only YYYY (→ Jan 1 or Dec 31)."""
    if not value:
        return None
    text = value.strip()
    if len(text) == 4 and text.isdigit():
        return f"{text}-12-31" if end else f"{text}-01-01"
    return text


def _aanstelling_van_year_sql(alias: str = "a") -> str:
    """Start year from text `van` (ISO date, year-only, or undated sentinel)."""
    van = f"{alias}.van"
    return f"""CASE
        WHEN {van} IS NULL OR TRIM({van}) IN ('', 'None') THEN NULL
        WHEN {van} ~ '^[0-9]{{4}}-' THEN SUBSTRING({van} FROM 1 FOR 4)::int
        WHEN {van} ~ '^[0-9]{{4}}$' THEN {van}::int
        ELSE NULL
    END"""


def _persoon_aanstelling_date_clauses(req: SearchRequest) -> tuple[list[str], dict]:
    """Persons with ≥1 appointment overlapping the van/tot window (legacy aanstellingsdatum)."""
    van = _normalize_filter_date(_date_filter(req.filters, "van"), end=False)
    tot = _normalize_filter_date(_date_filter(req.filters, "tot"), end=True)
    if not van and not tot:
        return [], {}
    period_sql = _period_clause("a", req.period, req.period_mode)
    parts = ["a.persoon_id = p.id", period_sql]
    params: dict = {}
    if van:
        # Appointment still open or ends on/after range start
        parts.append("(a.tot IS NULL OR a.tot >= :aanst_van)")
        params["aanst_van"] = van
    if tot:
        # Appointment started on/before range end (or undated start)
        parts.append("(a.van IS NULL OR a.van <= :aanst_tot)")
        params["aanst_tot"] = tot
    return [f"EXISTS (SELECT 1 FROM raa.aanstelling a WHERE {' AND '.join(parts)})"], params


def _int_ids(filters: dict[str, list[str]], key: str) -> list[int]:
    return [int(x) for x in filters.get(key, [])]


GEO_FILTER_COLUMNS = {
    "provincie_id": "provincie_id",
    "regio_id": "regio_id",
    "lokaal_id": "lokaal_id",
}


def _multi_fk_clauses(
    person_alias: str,
    column: str,
    ids: list[int],
    match: str,
    period: str | None,
    period_mode: str,
) -> list[str]:
    if not ids:
        return []
    if match == "all":
        clauses = []
        for i, id_val in enumerate(ids):
            alias = f"a_m{i}"
            period_sql = _period_clause(alias, period, period_mode)
            clauses.append(
                f"EXISTS (SELECT 1 FROM raa.aanstelling {alias} "
                f"WHERE {alias}.persoon_id = {person_alias}.id "
                f"AND {alias}.{column} = {id_val} AND {period_sql})"
            )
        return clauses
    id_list = ",".join(str(i) for i in ids)
    period_sql = _period_clause("a", period, period_mode)
    return [
        f"EXISTS (SELECT 1 FROM raa.aanstelling a "
        f"WHERE a.persoon_id = {person_alias}.id "
        f"AND a.{column} IN ({id_list}) AND {period_sql})"
    ]


def _aanstelling_multi_fk_clauses(
    appointment_alias: str,
    person_alias: str,
    column: str,
    ids: list[int],
    match: str,
    period: str | None,
    period_mode: str,
) -> list[str]:
    if not ids:
        return []
    if match == "all":
        clauses = []
        for i, id_val in enumerate(ids):
            alias = f"a_m{i}"
            period_sql = _period_clause(alias, period, period_mode)
            clauses.append(
                f"EXISTS (SELECT 1 FROM raa.aanstelling {alias} "
                f"WHERE {alias}.persoon_id = {person_alias}.id "
                f"AND {alias}.{column} = {id_val} AND {period_sql})"
            )
        return clauses
    id_list = ",".join(str(i) for i in ids)
    return [f"{appointment_alias}.{column} IN ({id_list})"]


def _stand_exists_clauses(person_alias: str, filters: dict[str, list[str]]) -> list[str]:
    stand_ids = _int_ids(filters, "stand_id")
    if not stand_ids:
        return []
    id_list = ",".join(str(i) for i in stand_ids)
    return [
        f"EXISTS (SELECT 1 FROM raa.aanstelling a "
        f"WHERE a.persoon_id = {person_alias}.id AND a.stand_id IN ({id_list}))"
    ]


def _adel_person_clause(filters: dict[str, list[str]]) -> list[str]:
    values = {v.strip().lower() for v in filters.get("adel", [])}
    if values & {"1", "true", "yes"}:
        return ["p.adel = 1"]
    return []


def _stand_aanstelling_clause(filters: dict[str, list[str]]) -> list[str]:
    stand_ids = _int_ids(filters, "stand_id")
    if not stand_ids:
        return []
    return [f"a.stand_id IN ({','.join(str(i) for i in stand_ids)})"]


def _adel_aanstelling_clause(filters: dict[str, list[str]]) -> list[str]:
    values = {v.strip().lower() for v in filters.get("adel", [])}
    if values & {"1", "true", "yes"}:
        return ["p.adel = 1"]
    return []


PERSONEN_SORT_COLUMNS = {
    "geslachtsnaam": (
        "COALESCE(NULLIF(TRIM(p.geslachtsnaam), ''), NULLIF(TRIM(p.voornaam), ''), '')"
    ),
    "voornaam": "p.voornaam",
    "geboortedatum": "p.geboortedatum",
    "overlijdensdatum": "p.overlijdensdatum",
}

AANSTELLINGEN_SORT_SQL = {
    "instelling": "i.naam, f.naam, p.geslachtsnaam",
    "functie": "f.naam, i.naam, p.geslachtsnaam",
    "van": "a.van NULLS LAST, i.naam, f.naam",
    "voornaam": "p.voornaam NULLS LAST, p.geslachtsnaam",
    "geslachtsnaam": "p.geslachtsnaam NULLS LAST, p.voornaam",
    "geboortedatum": "p.geboortedatum NULLS LAST, i.naam",
    "overlijdensdatum": "p.overlijdensdatum NULLS LAST, i.naam",
}


def list_stands(db: Session) -> list[dict]:
    rows = db.execute(
        text("SELECT stand_id AS id, naam FROM raa.stand ORDER BY naam")
    ).mappings().all()
    return [dict(r) for r in rows]


def _geo_exists_clauses(person_alias: str, filters: dict[str, list[str]]) -> list[str]:
    clauses = []
    for key, col in GEO_FILTER_COLUMNS.items():
        ids = _int_ids(filters, key)
        if ids:
            id_list = ",".join(str(i) for i in ids)
            clauses.append(
                f"EXISTS (SELECT 1 FROM raa.aanstelling a "
                f"WHERE a.persoon_id = {person_alias}.id AND a.{col} IN ({id_list}))"
            )
    return clauses


def _geo_aanstelling_clauses(filters: dict[str, list[str]]) -> list[str]:
    clauses = []
    for key, col in GEO_FILTER_COLUMNS.items():
        ids = _int_ids(filters, key)
        if ids:
            clauses.append(f"a.{col} IN ({','.join(str(i) for i in ids)})")
    return clauses


def _date_filter(filters: dict[str, list[str]], key: str) -> str | None:
    values = filters.get(key) or []
    return values[0] if values else None


def search_personen(db: Session, req: SearchRequest) -> SearchResponse:
    where_sql, params = _persoon_where(req)
    params = {**params, "limit": req.size, "offset": req.from_}
    sort_col = PERSONEN_SORT_COLUMNS.get(req.sort, PERSONEN_SORT_COLUMNS["geslachtsnaam"])
    direction = "DESC" if req.sort_dir == "desc" else "ASC"
    # Secondary key keeps ties stable when reversing direction
    secondary = "p.voornaam" if req.sort != "voornaam" else "p.id"
    order_sql = f"{sort_col} {direction} NULLS LAST, {secondary} ASC NULLS LAST"

    total = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM raa.persoon p WHERE {where_sql}"),
            params,
        ).scalar()
        or 0
    )

    rows = db.execute(
        text(
            f"""
            SELECT p.id, p.voornaam, p.tussenvoegsel, p.geslachtsnaam,
                   p.geboortedatum_als_bekend, p.overlijdensdatum_als_bekend, p.searchable,
                   p.geboorte_edtf, p.overlijden_edtf,
                   p.life_start_year, p.life_end_year,
                   p.life_start_source, p.life_end_source,
                   adt.naam AS adellijke_titel, act.naam AS academische_titel
            FROM raa.persoon p
            LEFT JOIN raa.adellijke_titel adt ON adt.id = p.adellijketitel_id
            LEFT JOIN raa.academische_titel act ON act.id = p.academischetitel_id
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    hits = []
    for row in rows:
        item = dict(row)
        item["display_naam"] = format_persoon_listing_name(item)
        hits.append(item)
    facets = _personen_facets(db, where_sql, params, req)
    timeline, timeline_meta = _personen_timeline(db, where_sql, params, req)
    return SearchResponse(
        hits=hits, total=total, facets=facets, timeline=timeline, timeline_meta=timeline_meta
    )


def summarize_personen(db: Session, req: SearchRequest) -> SummaryResponse:
    """Count + facet + timeline only (no hit rows) for overview charts."""
    where_sql, params = _persoon_where(req)
    total = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM raa.persoon p WHERE {where_sql}"),
            params,
        ).scalar()
        or 0
    )
    facets = _personen_facets(db, where_sql, params, req)
    timeline, timeline_meta = _personen_timeline(db, where_sql, params, req)
    return SummaryResponse(
        total=total, facets=facets, timeline=timeline, timeline_meta=timeline_meta
    )


def _personen_timeline(
    db: Session, where_sql: str, params: dict, req: SearchRequest
) -> tuple[list, TimelineMeta | None]:
    col = _year_column("geboorte", req.include_shadow_dates)
    undated = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM raa.persoon p WHERE {where_sql} AND {col} IS NULL"),
            params,
        ).scalar()
        or 0
    )
    field = "geboorte" if req.include_shadow_dates else "geboorte_exact"

    if req.period_mode == "overall":
        period_rows: dict[str, list[tuple[int, int]]] = {}
        for key, _label in PERIODS:
            match = _period_match_sql("p", key)
            rows = db.execute(
                text(
                    f"""
                    SELECT {col} AS y, COUNT(DISTINCT p.id)
                    FROM raa.persoon p
                    WHERE {where_sql} AND {col} IS NOT NULL AND {match}
                    GROUP BY 1
                    ORDER BY 1
                    """
                ),
                params,
            ).all()
            period_rows[key] = [(int(r[0]), int(r[1])) for r in rows]
        merged = merge_period_year_rows(period_rows)
        timeline, bin_mode = compress_stacked_timeline(merged)
        return timeline, TimelineMeta(
            field=field, bin=bin_mode, undated=undated, stacked=True
        )

    rows = db.execute(
        text(
            f"""
            SELECT {col} AS y, COUNT(DISTINCT p.id)
            FROM raa.persoon p
            WHERE {where_sql} AND {col} IS NOT NULL
            GROUP BY 1
            ORDER BY 1
            """
        ),
        params,
    ).all()
    timeline, bin_mode = compress_timeline([(int(r[0]), int(r[1])) for r in rows])
    return timeline, TimelineMeta(field=field, bin=bin_mode, undated=undated)


def _aanstelling_timeline(
    db: Session, where_sql: str, params: dict, req: SearchRequest
) -> tuple[list, TimelineMeta | None]:
    van_year = _aanstelling_van_year_sql("a")
    undated = int(
        db.execute(
            text(
                f"""
                SELECT COUNT(a.id)
                FROM raa.aanstelling a
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {where_sql} AND ({van_year}) IS NULL
                """
            ),
            params,
        ).scalar()
        or 0
    )

    if req.period_mode == "overall":
        period_rows: dict[str, list[tuple[int, int]]] = {}
        for key, _label in PERIODS:
            match = _period_match_sql("a", key)
            rows = db.execute(
                text(
                    f"""
                    SELECT {van_year} AS y, COUNT(a.id)
                    FROM raa.aanstelling a
                    JOIN raa.persoon p ON p.id = a.persoon_id
                    WHERE {where_sql} AND ({van_year}) IS NOT NULL AND {match}
                    GROUP BY 1
                    ORDER BY 1
                    """
                ),
                params,
            ).all()
            period_rows[key] = [(int(r[0]), int(r[1])) for r in rows]
        merged = merge_period_year_rows(period_rows)
        timeline, bin_mode = compress_stacked_timeline(merged)
        return timeline, TimelineMeta(
            field="aanstelling_van", bin=bin_mode, undated=undated, stacked=True
        )

    rows = db.execute(
        text(
            f"""
            SELECT {van_year} AS y, COUNT(a.id)
            FROM raa.aanstelling a
            JOIN raa.persoon p ON p.id = a.persoon_id
            WHERE {where_sql} AND ({van_year}) IS NOT NULL
            GROUP BY 1
            ORDER BY 1
            """
        ),
        params,
    ).all()
    timeline, bin_mode = compress_timeline([(int(r[0]), int(r[1])) for r in rows])
    return timeline, TimelineMeta(field="aanstelling_van", bin=bin_mode, undated=undated)


_PERSONEN_FACET_LIMIT = 20


def _personen_facet_base(
    req: SearchRequest, omit: set[str]
) -> tuple[str, dict]:
    return _persoon_where(req, omit_filter_keys=omit)


def _personen_facets(
    db: Session, where_sql: str, params: dict, req: SearchRequest
) -> dict[str, list[FacetValue]]:
    """Live facet counts for the current personen result set (disjunctive per dimension)."""
    facets: dict[str, list[FacetValue]] = {}
    period_sql = _period_clause("a", req.period, req.period_mode)

    if req.period_mode == "overall":
        period_facets = []
        for key, label in PERIODS:
            clause = f"{where_sql} AND {_period_match_sql('p', key)}"
            count = int(
                db.execute(
                    text(f"SELECT COUNT(*) FROM raa.persoon p WHERE {clause}"), params
                ).scalar()
                or 0
            )
            if count:
                period_facets.append(FacetValue(key=key, label=label, count=count))
        facets["period"] = period_facets

    stand_where, stand_params = _personen_facet_base(req, {"stand_id"})
    stand_rows = db.execute(
        text(
            f"""
            SELECT s.stand_id, s.naam, COUNT(DISTINCT p.id)
            FROM raa.persoon p
            JOIN raa.aanstelling a ON a.persoon_id = p.id AND {period_sql}
            JOIN raa.stand s ON s.stand_id = a.stand_id
            WHERE {stand_where}
            GROUP BY s.stand_id, s.naam
            ORDER BY COUNT(DISTINCT p.id) DESC, s.naam
            """
        ),
        stand_params,
    ).all()
    facets["stand"] = [
        FacetValue(key=str(row[0]), label=row[1], count=int(row[2])) for row in stand_rows
    ]

    adel_where, adel_params = _personen_facet_base(req, {"adel"})
    adel_count = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM raa.persoon p WHERE {adel_where} AND p.adel = 1"),
            adel_params,
        ).scalar()
        or 0
    )
    if adel_count:
        facets["adel"] = [FacetValue(key="1", label="Adel", count=adel_count)]

    for facet_key, table, join_col in (
        ("functie", "functie", "functie_id"),
        ("instelling", "instelling", "instelling_id"),
        ("provincie", "provincie", "provincie_id"),
        ("regio", "regio", "regio_id"),
        ("lokaal", "lokaal", "lokaal_id"),
    ):
        dim_where, dim_params = _personen_facet_base(req, {join_col})
        rows = db.execute(
            text(
                f"""
                SELECT t.id, t.naam, COUNT(DISTINCT p.id)
                FROM raa.persoon p
                JOIN raa.aanstelling a ON a.persoon_id = p.id AND {period_sql}
                JOIN raa.{table} t ON t.id = a.{join_col}
                WHERE {dim_where}
                GROUP BY t.id, t.naam
                ORDER BY COUNT(DISTINCT p.id) DESC, t.naam
                LIMIT {_PERSONEN_FACET_LIMIT}
                """
            ),
            dim_params,
        ).all()
        facets[facet_key] = [
            FacetValue(key=str(row[0]), label=row[1], count=int(row[2])) for row in rows
        ]

    return facets


_AANSTELLING_DETAIL_SQL = """
    SELECT a.id, a.van_als_bekend, a.tot_als_bekend, a.vertegenwoordigend, a.opmerkingen,
           f.id AS functie_id, f.naam AS functie,
           i.id AS instelling_id, i.naam AS instelling,
           pr.naam AS provincie, rg.naam AS regio, lk.naam AS lokaal, s.naam AS stand
    FROM raa.aanstelling a
    LEFT JOIN raa.functie f ON f.id = a.functie_id
    LEFT JOIN raa.instelling i ON i.id = a.instelling_id
    LEFT JOIN raa.provincie pr ON pr.id = a.provincie_id
    LEFT JOIN raa.regio rg ON rg.id = a.regio_id
    LEFT JOIN raa.lokaal lk ON lk.id = a.lokaal_id
    LEFT JOIN raa.stand s ON s.stand_id = a.stand_id
    WHERE a.persoon_id = :id
    ORDER BY a.van NULLS LAST, f.naam
"""


def _split_aanstellingen(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    lokaal: list[dict] = []
    bovenlokaal: list[dict] = []
    for row in rows:
        item = dict(row)
        if item.get("vertegenwoordigend"):
            lokaal.append(item)
        else:
            bovenlokaal.append(item)
    return lokaal, bovenlokaal


def get_persoon_detail(db: Session, person_id: int) -> dict | None:
    person = db.execute(
        text(
            """
            SELECT p.*,
                   adt.naam AS adellijke_titel,
                   act.naam AS academische_titel
            FROM raa.persoon p
            LEFT JOIN raa.adellijke_titel adt ON adt.id = p.adellijketitel_id
            LEFT JOIN raa.academische_titel act ON act.id = p.academischetitel_id
            WHERE p.id = :id
            """
        ),
        {"id": person_id},
    ).mappings().first()
    if not person:
        return None
    detail = dict(person)
    for field_name in EDITABLE_FIELDS.get("persoon", {}):
        base_val = detail.get(field_name)
        effective, amended = apply_effective_value(db, "persoon", person_id, field_name, base_val)
        if amended:
            detail[f"{field_name}_base"] = base_val
            detail[field_name] = effective
    detail["display_naam"] = format_persoon_naam(detail)
    detail["listing_naam"] = format_persoon_listing_name(detail)
    detail["life_summary"] = format_persoon_life_summary(detail)
    detail["heerlijkheid_line"] = format_heerlijkheid(detail)
    detail["opmerkingen_html"] = format_opmerkingen_html(detail.get("opmerkingen"))
    detail["aliassen"] = [
        dict(r)
        for r in db.execute(
            text("SELECT naam FROM raa.alias WHERE persoon_id = :id ORDER BY naam"),
            {"id": person_id},
        ).mappings().all()
    ]
    detail["bronnen"] = [
        dict(r)
        for r in db.execute(
            text(
                """
                SELECT b.naam, bd.details
                FROM raa.bron_details bd
                JOIN raa.bron b ON b.id = bd.bron_id
                WHERE bd.persoon_id = :id
                ORDER BY b.naam
                """
            ),
            {"id": person_id},
        ).mappings().all()
    ]
    aanstellingen = [
        dict(r)
        for r in db.execute(text(_AANSTELLING_DETAIL_SQL), {"id": person_id}).mappings().all()
    ]
    for a in aanstellingen:
        oid = int(a["id"])
        base_opm = a.get("opmerkingen")
        effective, amended = apply_effective_value(db, "aanstelling", oid, "opmerkingen", base_opm)
        if amended:
            a["opmerkingen_base"] = base_opm
            a["opmerkingen"] = effective
        if a.get("opmerkingen"):
            a["opmerkingen_html"] = format_opmerkingen_html(a["opmerkingen"])
    lokaal, bovenlokaal = _split_aanstellingen(aanstellingen)
    detail["aanstellingen_lokaal"] = lokaal
    detail["aanstellingen_bovenlokaal"] = bovenlokaal
    detail["aanstellingen"] = aanstellingen
    return detail


def list_periods(db: Session, context: str = "personen") -> list[PeriodCount]:
    table = {
        "personen": "persoon",
        "aanstellingen": "aanstelling",
        "instellingen": "instelling",
        "functies": "functie",
    }.get(context, "persoon")
    result = []
    for key, label in PERIODS:
        count = int(
            db.execute(
                text(f"SELECT COUNT(*) FROM raa.{table} t WHERE {_period_match_sql('t', key)}")
            ).scalar()
            or 0
        )
        result.append(PeriodCount(key=key, label=label, count=count))
    return result


def _aanstelling_where(
    req: SearchRequest, *, omit_filter_keys: set[str] | None = None
) -> tuple[str, dict]:
    omit = omit_filter_keys or set()
    where = [_period_clause("a", req.period, req.period_mode)]
    params: dict = {}

    if "functie_id" not in omit:
        functie_ids = _int_ids(req.filters, "functie_id")
        if functie_ids:
            where.extend(
                _aanstelling_multi_fk_clauses(
                    "a",
                    "p",
                    "functie_id",
                    functie_ids,
                    req.functie_match,
                    req.period,
                    req.period_mode,
                )
            )

    if "instelling_id" not in omit:
        instelling_ids = _int_ids(req.filters, "instelling_id")
        if instelling_ids:
            where.extend(
                _aanstelling_multi_fk_clauses(
                    "a",
                    "p",
                    "instelling_id",
                    instelling_ids,
                    req.instelling_match,
                    req.period,
                    req.period_mode,
                )
            )

    van = _normalize_filter_date(_date_filter(req.filters, "van"), end=False)
    if van:
        where.append("a.van >= :van")
        params["van"] = van
    tot = _normalize_filter_date(_date_filter(req.filters, "tot"), end=True)
    if tot:
        where.append("a.tot <= :tot")
        params["tot"] = tot

    if req.q:
        patterns = text_search_patterns(req.q)
        person_clauses = []
        for i, pattern in enumerate(patterns):
            key = f"q{i}"
            person_clauses.append(_persoon_text_token_clause(key))
            params[key] = pattern
        where.append(f"({' AND '.join(person_clauses)})")

    geo_filters = (
        {k: v for k, v in req.filters.items() if k not in omit} if omit else req.filters
    )
    where.extend(_geo_aanstelling_clauses(geo_filters))
    if "stand_id" not in omit:
        where.extend(_stand_aanstelling_clause(req.filters))
    if "adel" not in omit:
        where.extend(_adel_aanstelling_clause(req.filters))

    return " AND ".join(where), params


_AANSTELLING_FACET_LIMIT = 20


def _aanstelling_facets(
    db: Session, where_sql: str, params: dict, req: SearchRequest
) -> dict[str, list[FacetValue]]:
    """Live facet counts for aanstellingen (disjunctive per dimension)."""
    del where_sql, params  # rebuild per dimension
    facets: dict[str, list[FacetValue]] = {}

    for facet_key, table, join_col in (
        ("functie", "functie", "functie_id"),
        ("instelling", "instelling", "instelling_id"),
        ("provincie", "provincie", "provincie_id"),
        ("regio", "regio", "regio_id"),
        ("lokaal", "lokaal", "lokaal_id"),
    ):
        dim_where, dim_params = _aanstelling_where(req, omit_filter_keys={join_col})
        rows = db.execute(
            text(
                f"""
                SELECT t.id, t.naam, COUNT(a.id)
                FROM raa.aanstelling a
                JOIN raa.persoon p ON p.id = a.persoon_id
                JOIN raa.{table} t ON t.id = a.{join_col}
                WHERE {dim_where}
                GROUP BY t.id, t.naam
                ORDER BY COUNT(a.id) DESC, t.naam
                LIMIT {_AANSTELLING_FACET_LIMIT}
                """
            ),
            dim_params,
        ).all()
        facets[facet_key] = [
            FacetValue(key=str(row[0]), label=row[1], count=int(row[2])) for row in rows
        ]

    stand_where, stand_params = _aanstelling_where(req, omit_filter_keys={"stand_id"})
    stand_rows = db.execute(
        text(
            f"""
            SELECT s.stand_id, s.naam, COUNT(a.id)
            FROM raa.aanstelling a
            JOIN raa.stand s ON s.stand_id = a.stand_id
            JOIN raa.persoon p ON p.id = a.persoon_id
            WHERE {stand_where}
            GROUP BY s.stand_id, s.naam
            ORDER BY COUNT(a.id) DESC, s.naam
            """
        ),
        stand_params,
    ).all()
    facets["stand"] = [
        FacetValue(key=str(row[0]), label=row[1], count=int(row[2])) for row in stand_rows
    ]

    adel_where, adel_params = _aanstelling_where(req, omit_filter_keys={"adel"})
    adel_count = int(
        db.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM raa.aanstelling a
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {adel_where} AND p.adel = 1
                """
            ),
            adel_params,
        ).scalar()
        or 0
    )
    if adel_count:
        facets["adel"] = [FacetValue(key="1", label="Adel", count=adel_count)]
    return facets


def search_aanstellingen(db: Session, req: SearchRequest) -> SearchResponse:
    where_sql, params = _aanstelling_where(req)
    params = {**params, "limit": req.size, "offset": req.from_}

    if req.group_by == "instelling":
        total = int(
            db.execute(
                text(
                    f"""
                    SELECT COUNT(*) FROM (
                        SELECT i.id
                        FROM raa.aanstelling a
                        JOIN raa.instelling i ON i.id = a.instelling_id
                        JOIN raa.persoon p ON p.id = a.persoon_id
                        WHERE {where_sql}
                        GROUP BY i.id
                    ) grouped
                    """
                ),
                params,
            ).scalar()
            or 0
        )
        rows = db.execute(
            text(
                f"""
                SELECT i.id, i.naam, COUNT(a.id) AS count
                FROM raa.aanstelling a
                JOIN raa.instelling i ON i.id = a.instelling_id
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {where_sql}
                GROUP BY i.id, i.naam
                ORDER BY i.naam
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        ).mappings().all()
        hits = [dict(row) for row in rows]
        return SearchResponse(hits=hits, total=total, facets={})

    if req.group_by == "functie":
        total = int(
            db.execute(
                text(
                    f"""
                    SELECT COUNT(*) FROM (
                        SELECT f.id
                        FROM raa.aanstelling a
                        JOIN raa.functie f ON f.id = a.functie_id
                        JOIN raa.persoon p ON p.id = a.persoon_id
                        WHERE {where_sql}
                        GROUP BY f.id
                    ) grouped
                    """
                ),
                params,
            ).scalar()
            or 0
        )
        rows = db.execute(
            text(
                f"""
                SELECT f.id, f.naam, COUNT(a.id) AS count
                FROM raa.aanstelling a
                JOIN raa.functie f ON f.id = a.functie_id
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {where_sql}
                GROUP BY f.id, f.naam
                ORDER BY f.naam
                LIMIT :limit OFFSET :offset
                """
            ),
            params,
        ).mappings().all()
        hits = [dict(row) for row in rows]
        return SearchResponse(hits=hits, total=total, facets={})

    total = int(
        db.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM raa.aanstelling a
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {where_sql}
                """
            ),
            params,
        ).scalar()
        or 0
    )
    order_sql = AANSTELLINGEN_SORT_SQL.get(req.sort, AANSTELLINGEN_SORT_SQL["van"])
    rows = db.execute(
        text(
            f"""
            SELECT a.id, a.van_als_bekend, a.tot_als_bekend,
                   p.id AS persoon_id, p.voornaam, p.tussenvoegsel, p.geslachtsnaam,
                   f.id AS functie_id, f.naam AS functie,
                   i.id AS instelling_id, i.naam AS instelling
            FROM raa.aanstelling a
            JOIN raa.persoon p ON p.id = a.persoon_id
            JOIN raa.functie f ON f.id = a.functie_id
            JOIN raa.instelling i ON i.id = a.instelling_id
            WHERE {where_sql}
            ORDER BY {order_sql}
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    hits = [dict(row) for row in rows]
    facets = _aanstelling_facets(db, where_sql, params, req)
    timeline, timeline_meta = _aanstelling_timeline(db, where_sql, params, req)
    return SearchResponse(
        hits=hits, total=total, facets=facets, timeline=timeline, timeline_meta=timeline_meta
    )


def summarize_aanstellingen(db: Session, req: SearchRequest) -> SummaryResponse:
    """Count + facet + timeline for flat aanstelling rows (overview charts)."""
    where_sql, params = _aanstelling_where(req)
    total = int(
        db.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM raa.aanstelling a
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {where_sql}
                """
            ),
            params,
        ).scalar()
        or 0
    )
    facets = _aanstelling_facets(db, where_sql, params, req)
    timeline, timeline_meta = _aanstelling_timeline(db, where_sql, params, req)
    return SummaryResponse(
        total=total, facets=facets, timeline=timeline, timeline_meta=timeline_meta
    )


def _named_entity_where(prefix: str, req: SearchRequest) -> tuple[str, dict]:
    where = [_period_clause(prefix, req.period, req.period_mode)]
    params: dict = {}
    if req.q:
        patterns = text_search_patterns(req.q)
        for i, pattern in enumerate(patterns):
            key = f"q{i}"
            where.append(f"{prefix}.naam ILIKE :{key}")
            params[key] = pattern
    return " AND ".join(where), params


def search_instellingen(db: Session, req: SearchRequest) -> SearchResponse:
    where_sql, params = _named_entity_where("i", req)
    params = {**params, "limit": req.size, "offset": req.from_}
    total = int(
        db.execute(text(f"SELECT COUNT(*) FROM raa.instelling i WHERE {where_sql}"), params).scalar() or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT i.id, i.naam,
                   (SELECT COUNT(*) FROM raa.aanstelling a WHERE a.instelling_id = i.id) AS aanstelling_count
            FROM raa.instelling i
            WHERE {where_sql}
            ORDER BY i.naam
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    return SearchResponse(hits=[dict(r) for r in rows], total=total)


def search_functies(db: Session, req: SearchRequest) -> SearchResponse:
    where_sql, params = _named_entity_where("f", req)
    params = {**params, "limit": req.size, "offset": req.from_}
    total = int(
        db.execute(text(f"SELECT COUNT(*) FROM raa.functie f WHERE {where_sql}"), params).scalar() or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT f.id, f.naam,
                   (SELECT COUNT(*) FROM raa.aanstelling a WHERE a.functie_id = f.id) AS aanstelling_count
            FROM raa.functie f
            WHERE {where_sql}
            ORDER BY f.naam
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    return SearchResponse(hits=[dict(r) for r in rows], total=total)


def get_instelling_detail(db: Session, instelling_id: int) -> dict | None:
    row = db.execute(
        text("SELECT id, naam, toelichting FROM raa.instelling WHERE id = :id"),
        {"id": instelling_id},
    ).mappings().first()
    if not row:
        return None
    detail = dict(row)
    from raa_api.editorial import apply_effective_value

    base_toelichting = detail.get("toelichting")
    effective, amended = apply_effective_value(
        db, "instelling", instelling_id, "toelichting", base_toelichting
    )
    detail["toelichting_base"] = base_toelichting
    detail["toelichting"] = effective
    detail["toelichting_amended"] = amended
    aanstelling_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM raa.aanstelling WHERE instelling_id = :id"),
            {"id": instelling_id},
        ).scalar()
        or 0
    )
    functies = [
        dict(r)
        for r in db.execute(
            text(
                """
                SELECT f.id, f.naam, COUNT(a.id) AS aanstelling_count
                FROM raa.functie f
                JOIN raa.aanstelling a ON a.functie_id = f.id
                WHERE a.instelling_id = :id
                GROUP BY f.id, f.naam
                ORDER BY f.naam
                """
            ),
            {"id": instelling_id},
        ).mappings().all()
    ]
    detail["aanstelling_count"] = aanstelling_count
    detail["functies"] = functies
    spans = _instelling_functie_spans(db, instelling_id)
    span_summary = None
    try:
        span_summary = db.execute(
            text(
                """
                SELECT MIN(first_year) AS first_year, MAX(last_year) AS last_year,
                       COUNT(DISTINCT functie_id) AS functie_count
                FROM raa.functie_instelling_span
                WHERE instelling_id = :id
                """
            ),
            {"id": instelling_id},
        ).mappings().first()
    except ProgrammingError:
        db.rollback()

    stats: list[dict] = [
        {"label": "Aanstellingen", "value": aanstelling_count},
        {"label": "Functies in bestand", "value": len(functies)},
    ]
    if span_summary and span_summary["first_year"] is not None:
        stats.append(
            {
                "label": "Eerste gedateerde aanstelling",
                "value": str(int(span_summary["first_year"])),
            }
        )
    if span_summary and span_summary["last_year"] is not None:
        stats.append(
            {
                "label": "Laatste gedateerde aanstelling",
                "value": str(int(span_summary["last_year"])),
            }
        )

    context_items = [
        {
            "naam": s["functie_naam"],
            "href": (
                f"/aanstellingen?functie_id={s['functie_id']}"
                f"&instelling_id={instelling_id}"
            ),
            "aanstelling_count": s["aanstelling_count"],
            "meta": s.get("span_label"),
        }
        for s in spans
    ] or [
        {
            **f,
            "href": f"/aanstellingen?functie_id={f['id']}&instelling_id={instelling_id}",
        }
        for f in functies
    ]

    detail["profile"] = entity_profile(
        entity_type="instelling",
        entity_id=instelling_id,
        naam=detail["naam"],
        stats=stats,
        related=[
            {
                "title": "Functies in deze instelling",
                "entity_type": "functie",
                "items": context_items,
            }
        ],
        sections=[
            {
                "title": "Institutionele toelichting",
                "html": format_opmerkingen_html(detail.get("toelichting")),
            },
            {"title": "Toelichting bij datums", "html": ENTITY_SPAN_CAVEAT_HTML},
        ],
    )
    return detail


def _functie_attestation_row(db: Session, functie_id: int) -> dict | None:
    try:
        row = db.execute(
            text("SELECT * FROM raa.functie_attestation WHERE functie_id = :id"),
            {"id": functie_id},
        ).mappings().first()
    except ProgrammingError:
        db.rollback()
        return None
    return dict(row) if row else None


def _functie_instelling_spans(db: Session, functie_id: int) -> list[dict]:
    try:
        rows = db.execute(
            text(
                """
                SELECT *
                FROM raa.functie_instelling_span
                WHERE functie_id = :id
                ORDER BY first_year NULLS LAST, instelling_naam
                """
            ),
            {"id": functie_id},
        ).mappings().all()
    except ProgrammingError:
        db.rollback()
        return []
    return [dict(r) for r in rows]


def _instelling_functie_spans(db: Session, instelling_id: int) -> list[dict]:
    try:
        rows = db.execute(
            text(
                """
                SELECT s.*, f.naam AS functie_naam
                FROM raa.functie_instelling_span s
                JOIN raa.functie f ON f.id = s.functie_id
                WHERE s.instelling_id = :id
                ORDER BY f.naam, s.first_year NULLS LAST
                """
            ),
            {"id": instelling_id},
        ).mappings().all()
    except ProgrammingError:
        db.rollback()
        return []
    return [dict(r) for r in rows]


def get_functie_detail(db: Session, functie_id: int) -> dict | None:
    row = db.execute(
        text("SELECT id, naam FROM raa.functie WHERE id = :id"),
        {"id": functie_id},
    ).mappings().first()
    if not row:
        return None
    detail = dict(row)
    aanstelling_count = int(
        db.execute(
            text("SELECT COUNT(*) FROM raa.aanstelling WHERE functie_id = :id"),
            {"id": functie_id},
        ).scalar()
        or 0
    )
    persoon_count = int(
        db.execute(
            text("SELECT COUNT(DISTINCT persoon_id) FROM raa.aanstelling WHERE functie_id = :id"),
            {"id": functie_id},
        ).scalar()
        or 0
    )
    instellingen = [
        dict(r)
        for r in db.execute(
            text(
                """
                SELECT i.id, i.naam, COUNT(a.id) AS aanstelling_count
                FROM raa.instelling i
                JOIN raa.aanstelling a ON a.instelling_id = i.id
                WHERE a.functie_id = :id
                GROUP BY i.id, i.naam
                ORDER BY i.naam
                LIMIT 50
                """
            ),
            {"id": functie_id},
        ).mappings().all()
    ]
    detail["aanstelling_count"] = aanstelling_count
    detail["persoon_count"] = persoon_count
    detail["instellingen"] = instellingen
    attestation = _functie_attestation_row(db, functie_id)
    spans = _functie_instelling_spans(db, functie_id)

    stats: list[dict] = [
        {"label": "Aanstellingen", "value": aanstelling_count},
        {"label": "Personen", "value": persoon_count},
        {"label": "Instellingen", "value": attestation["instelling_count"] if attestation else len(instellingen)},
    ]
    if attestation:
        stats.extend(
            [
                {
                    "label": "Eerste gedateerde aanstelling",
                    "html": format_corpus_witness(
                        attestation.get("corpus_first_year"),
                        attestation.get("corpus_first_instelling_naam"),
                        attestation.get("corpus_first_instelling_id"),
                    ),
                },
                {
                    "label": "Laatste gedateerde aanstelling",
                    "html": format_corpus_witness(
                        attestation.get("corpus_last_year"),
                        attestation.get("corpus_last_instelling_naam"),
                        attestation.get("corpus_last_instelling_id"),
                    ),
                },
            ]
        )

    context_items = [
        {
            "naam": s["instelling_naam"],
            "href": (
                f"/aanstellingen?functie_id={functie_id}"
                f"&instelling_id={s['instelling_id']}"
            ),
            "aanstelling_count": s["aanstelling_count"],
            "meta": s.get("span_label"),
        }
        for s in spans
    ] or [
        {
            **i,
            "href": f"/aanstellingen?functie_id={functie_id}&instelling_id={i['id']}",
        }
        for i in instellingen
    ]

    detail["profile"] = entity_profile(
        entity_type="functie",
        entity_id=functie_id,
        naam=detail["naam"],
        stats=stats,
        actions=[
            {
                "label": "Aanstellingen voor deze functie…",
                "href": f"/aanstellingen?functie_id={functie_id}",
            },
            {
                "label": "Personen die deze functie bekleedden…",
                "href": f"/personen?functie_id={functie_id}",
            },
        ],
        sections=[{"title": "Toelichting bij datums", "html": ENTITY_SPAN_CAVEAT_HTML}] if attestation else [],
        related=[
            {
                "title": "Institutionele contexten",
                "entity_type": "instelling",
                "items": context_items,
            }
        ],
    )
    return detail


def suggest_field(db: Session, field: str, q: str, period: str | None, mode: str) -> list[dict]:
    period_clause = _period_clause("a", period, mode)
    geo_suggest = {
        "provincie": ("raa.provincie", "pr", "provincie_id"),
        "regio": ("raa.regio", "rg", "regio_id"),
        "lokaal": ("raa.lokaal", "lk", "lokaal_id"),
    }
    if field in geo_suggest:
        table, alias, fk = geo_suggest[field]
        rows = db.execute(
            text(
                f"""
                SELECT DISTINCT {alias}.id, {alias}.naam
                FROM {table} {alias}
                JOIN raa.aanstelling a ON a.{fk} = {alias}.id
                WHERE {alias}.naam ILIKE :q AND {period_clause}
                ORDER BY {alias}.naam
                LIMIT 20
                """
            ),
            {"q": f"%{q}%"},
        ).mappings().all()
        return [dict(r) for r in rows]
    if field == "functie":
        rows = db.execute(
            text(
                f"""
                SELECT DISTINCT f.id, f.naam
                FROM raa.functie f
                JOIN raa.aanstelling a ON a.functie_id = f.id
                WHERE f.naam ILIKE :q AND {period_clause}
                ORDER BY f.naam
                LIMIT 20
                """
            ),
            {"q": f"%{q}%"},
        ).mappings().all()
        return [dict(r) for r in rows]
    if field == "instelling":
        rows = db.execute(
            text(
                f"""
                SELECT DISTINCT i.id, i.naam
                FROM raa.instelling i
                JOIN raa.aanstelling a ON a.instelling_id = i.id
                WHERE i.naam ILIKE :q AND {period_clause}
                ORDER BY i.naam
                LIMIT 20
                """
            ),
            {"q": f"%{q}%"},
        ).mappings().all()
        return [dict(r) for r in rows]
    return []


def browse_az(
    db: Session,
    entity: str,
    *,
    letter: str | None = None,
    period: str | None = None,
    period_mode: str = "scoped",
    from_: int = 0,
    size: int = 100,
) -> dict:
    """Period-scoped A–Z catalog for instelling, functie, or persoon (geslachtsnaam)."""
    if entity == "personen":
        return _browse_personen_az(
            db,
            letter=letter,
            period=period,
            period_mode=period_mode,
            from_=from_,
            size=size,
        )
    if entity == "instellingen":
        table, alias, count_fk = "raa.instelling", "t", "instelling_id"
    elif entity == "functies":
        table, alias, count_fk = "raa.functie", "t", "functie_id"
    else:
        raise ValueError(f"Unsupported browse entity: {entity}")

    period_sql = _period_clause(alias, period, period_mode)
    where = [period_sql]
    params: dict = {"limit": size, "offset": from_}

    letter_key = (letter or "").strip().upper()
    if letter_key and letter_key != "ALL":
        if letter_key == "#":
            where.append(f"LEFT(UPPER({alias}.naam), 1) !~ '^[A-Z]$'")
        elif len(letter_key) == 1 and letter_key.isalpha():
            where.append(f"UPPER({alias}.naam) LIKE :letter_prefix")
            params["letter_prefix"] = f"{letter_key}%"

    where_sql = " AND ".join(where)
    total = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM {table} {alias} WHERE {where_sql}"),
            params,
        ).scalar()
        or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT {alias}.id, {alias}.naam,
                   (SELECT COUNT(*) FROM raa.aanstelling a WHERE a.{count_fk} = {alias}.id) AS aanstelling_count
            FROM {table} {alias}
            WHERE {where_sql}
            ORDER BY {alias}.naam
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    letter_rows = db.execute(
        text(
            f"""
            SELECT
              CASE
                WHEN LEFT(UPPER({alias}.naam), 1) ~ '^[A-Z]$'
                  THEN LEFT(UPPER({alias}.naam), 1)
                ELSE '#'
              END AS letter,
              COUNT(*) AS count
            FROM {table} {alias}
            WHERE {period_sql}
            GROUP BY 1
            ORDER BY 1
            """
        ),
    ).all()
    letters = [{"letter": row[0], "count": int(row[1])} for row in letter_rows]
    return {
        "hits": [dict(r) for r in rows],
        "total": total,
        "letter": letter_key or "ALL",
        "letters": letters,
    }


_PERSON_SORT_NAME = (
    "COALESCE(NULLIF(TRIM(p.geslachtsnaam), ''), NULLIF(TRIM(p.voornaam), ''), '')"
)
_PERSON_LETTER = f"LEFT(UPPER({_PERSON_SORT_NAME}), 1)"


def _browse_personen_az(
    db: Session,
    *,
    letter: str | None = None,
    period: str | None = None,
    period_mode: str = "scoped",
    from_: int = 0,
    size: int = 100,
) -> dict:
    """A–Z by geslachtsnaam (fallback voornaam when empty — D-37)."""
    period_sql = _period_clause("p", period, period_mode)
    where = [period_sql]
    params: dict = {"limit": size, "offset": from_}
    letter_key = (letter or "").strip().upper()
    if letter_key and letter_key != "ALL":
        if letter_key == "#":
            where.append(f"({_PERSON_LETTER} = '' OR {_PERSON_LETTER} !~ '^[A-Z]$')")
        elif len(letter_key) == 1 and letter_key.isalpha():
            where.append(f"{_PERSON_LETTER} = :naam_letter")
            params["naam_letter"] = letter_key

    where_sql = " AND ".join(where)
    total = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM raa.persoon p WHERE {where_sql}"),
            params,
        ).scalar()
        or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT p.id, p.voornaam, p.tussenvoegsel, p.geslachtsnaam,
                   p.geboortedatum_als_bekend, p.overlijdensdatum_als_bekend,
                   p.geboorte_edtf, p.overlijden_edtf,
                   p.life_start_year, p.life_end_year,
                   p.life_start_source, p.life_end_source,
                   adt.naam AS adellijke_titel, act.naam AS academische_titel
            FROM raa.persoon p
            LEFT JOIN raa.adellijke_titel adt ON adt.id = p.adellijketitel_id
            LEFT JOIN raa.academische_titel act ON act.id = p.academischetitel_id
            WHERE {where_sql}
            ORDER BY {_PERSON_SORT_NAME} NULLS LAST, p.voornaam NULLS LAST
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    hits = []
    for row in rows:
        item = dict(row)
        item["display_naam"] = format_persoon_listing_name(item)
        hits.append(item)

    letter_rows = db.execute(
        text(
            f"""
            SELECT
              CASE
                WHEN {_PERSON_LETTER} ~ '^[A-Z]$' THEN {_PERSON_LETTER}
                ELSE '#'
              END AS letter,
              COUNT(*) AS count
            FROM raa.persoon p
            WHERE {period_sql}
            GROUP BY 1
            ORDER BY 1
            """
        ),
    ).all()
    letters = [{"letter": row[0], "count": int(row[1])} for row in letter_rows]
    return {
        "hits": hits,
        "total": total,
        "letter": letter_key or "ALL",
        "letters": letters,
    }