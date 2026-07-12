from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from raa_api.config import PERIODS
from raa_api.schemas import FacetValue, PeriodCount, SearchRequest, SearchResponse, text_search_patterns

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


def _persoon_where(req: SearchRequest) -> tuple[str, dict]:
    where = [_period_clause("p", req.period, req.period_mode)]
    params: dict = {}

    if req.q:
        patterns = text_search_patterns(req.q)
        for i, pattern in enumerate(patterns):
            key = f"q{i}"
            where.append(
                f"(p.searchable ILIKE :{key} OR p.geslachtsnaam ILIKE :{key} "
                f"OR p.voornaam ILIKE :{key})"
            )
            params[key] = pattern

    if req.filters.get("instelling_id"):
        ids = req.filters["instelling_id"]
        where.append(
            "EXISTS (SELECT 1 FROM raa.aanstelling a "
            "WHERE a.persoon_id = p.id "
            f"AND a.instelling_id IN ({','.join(str(int(x)) for x in ids)}))"
        )

    if req.filters.get("functie_id"):
        ids = req.filters["functie_id"]
        where.append(
            "EXISTS (SELECT 1 FROM raa.aanstelling a "
            "WHERE a.persoon_id = p.id "
            f"AND a.functie_id IN ({','.join(str(int(x)) for x in ids)}))"
        )

    where.extend(_geo_exists_clauses("p", req.filters))

    return " AND ".join(where), params


def _int_ids(filters: dict[str, list[str]], key: str) -> list[int]:
    return [int(x) for x in filters.get(key, [])]


GEO_FILTER_COLUMNS = {
    "provincie_id": "provincie_id",
    "regio_id": "regio_id",
    "lokaal_id": "lokaal_id",
}


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
    sort_col = req.sort if req.sort in {"geslachtsnaam", "voornaam", "geboortedatum"} else "geslachtsnaam"

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
                   p.geboortedatum_als_bekend, p.overlijdensdatum_als_bekend, p.searchable
            FROM raa.persoon p
            WHERE {where_sql}
            ORDER BY p.{sort_col} NULLS LAST
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    hits = [dict(row) for row in rows]
    facets = _personen_facets(db, where_sql, params, req)
    return SearchResponse(hits=hits, total=total, facets=facets)


def _personen_facets(
    db: Session, where_sql: str, params: dict, req: SearchRequest
) -> dict[str, list[FacetValue]]:
    facets: dict[str, list[FacetValue]] = {}
    if req.period_mode == "overall":
        period_facets = []
        for key, label in PERIODS:
            clause = f"{where_sql} AND {_period_match_sql('p', key)}"
            count = int(
                db.execute(text(f"SELECT COUNT(*) FROM raa.persoon p WHERE {clause}"), params).scalar() or 0
            )
            period_facets.append(FacetValue(key=key, label=label, count=count))
        facets["period"] = period_facets

    stand_rows = db.execute(
        text(
            f"""
            SELECT s.naam, COUNT(DISTINCT p.id)
            FROM raa.persoon p
            JOIN raa.aanstelling a ON a.persoon_id = p.id
            JOIN raa.stand s ON s.stand_id = a.stand_id
            WHERE {where_sql}
            GROUP BY s.naam
            ORDER BY s.naam
            """
        ),
        params,
    ).all()
    facets["stand"] = [
        FacetValue(key=row[0], label=row[0], count=int(row[1])) for row in stand_rows
    ]
    return facets


def get_persoon_detail(db: Session, person_id: int) -> dict | None:
    person = db.execute(
        text("SELECT * FROM raa.persoon WHERE id = :id"),
        {"id": person_id},
    ).mappings().first()
    if not person:
        return None
    detail = dict(person)
    detail["aliassen"] = [
        dict(r)
        for r in db.execute(
            text("SELECT naam FROM raa.alias WHERE persoon_id = :id ORDER BY naam"),
            {"id": person_id},
        ).mappings().all()
    ]
    detail["aanstellingen"] = [
        dict(r)
        for r in db.execute(
            text(
                """
                SELECT a.id, a.van_als_bekend, a.tot_als_bekend,
                       f.naam AS functie, i.naam AS instelling
                FROM raa.aanstelling a
                LEFT JOIN raa.functie f ON f.id = a.functie_id
                LEFT JOIN raa.instelling i ON i.id = a.instelling_id
                WHERE a.persoon_id = :id
                ORDER BY a.van NULLS LAST, f.naam
                """
            ),
            {"id": person_id},
        ).mappings().all()
    ]
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


def _aanstelling_where(req: SearchRequest) -> tuple[str, dict]:
    where = [_period_clause("a", req.period, req.period_mode)]
    params: dict = {}

    for key, col in (("functie_id", "a.functie_id"), ("instelling_id", "a.instelling_id")):
        ids = _int_ids(req.filters, key)
        if ids:
            where.append(f"{col} IN ({','.join(str(i) for i in ids)})")

    van = _date_filter(req.filters, "van")
    if van:
        where.append("a.van >= :van")
        params["van"] = van
    tot = _date_filter(req.filters, "tot")
    if tot:
        where.append("a.tot <= :tot")
        params["tot"] = tot

    if req.q:
        patterns = text_search_patterns(req.q)
        person_clauses = []
        for i, pattern in enumerate(patterns):
            key = f"q{i}"
            person_clauses.append(
                f"(p.searchable ILIKE :{key} OR p.geslachtsnaam ILIKE :{key} OR p.voornaam ILIKE :{key})"
            )
            params[key] = pattern
        where.append(f"({' AND '.join(person_clauses)})")

    where.extend(_geo_aanstelling_clauses(req.filters))

    return " AND ".join(where), params


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
            ORDER BY i.naam, f.naam, p.geslachtsnaam
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    hits = [dict(row) for row in rows]
    facets = _aanstelling_facets(db, where_sql, params, req)
    return SearchResponse(hits=hits, total=total, facets=facets)


def _aanstelling_facets(
    db: Session, where_sql: str, params: dict, req: SearchRequest
) -> dict[str, list[FacetValue]]:
    facets: dict[str, list[FacetValue]] = {}
    if not _int_ids(req.filters, "functie_id"):
        functie_rows = db.execute(
            text(
                f"""
                SELECT f.naam, COUNT(a.id)
                FROM raa.aanstelling a
                JOIN raa.functie f ON f.id = a.functie_id
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {where_sql}
                GROUP BY f.naam
                ORDER BY f.naam
                LIMIT 50
                """
            ),
            params,
        ).all()
        facets["functie"] = [
            FacetValue(key=row[0], label=row[0], count=int(row[1])) for row in functie_rows
        ]
    if not _int_ids(req.filters, "instelling_id"):
        inst_rows = db.execute(
            text(
                f"""
                SELECT i.naam, COUNT(a.id)
                FROM raa.aanstelling a
                JOIN raa.instelling i ON i.id = a.instelling_id
                JOIN raa.persoon p ON p.id = a.persoon_id
                WHERE {where_sql}
                GROUP BY i.naam
                ORDER BY i.naam
                LIMIT 50
                """
            ),
            params,
        ).all()
        facets["instelling"] = [
            FacetValue(key=row[0], label=row[0], count=int(row[1])) for row in inst_rows
        ]
    return facets


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
    detail["aanstelling_count"] = int(
        db.execute(
            text("SELECT COUNT(*) FROM raa.aanstelling WHERE instelling_id = :id"),
            {"id": instelling_id},
        ).scalar()
        or 0
    )
    return detail


def get_functie_detail(db: Session, functie_id: int) -> dict | None:
    row = db.execute(
        text("SELECT id, naam FROM raa.functie WHERE id = :id"),
        {"id": functie_id},
    ).mappings().first()
    if not row:
        return None
    detail = dict(row)
    detail["aanstelling_count"] = int(
        db.execute(
            text("SELECT COUNT(*) FROM raa.aanstelling WHERE functie_id = :id"),
            {"id": functie_id},
        ).scalar()
        or 0
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
