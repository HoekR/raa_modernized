from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from raa_api.auth import require_editor
from raa_api.config import editorial_settings
from raa_api.db import get_db
from raa_api.editorial import (
    ensure_editorial_schema,
    entity_exists,
    get_entity_edit_context,
    get_instelling_toelichting_edit_context,
    list_amendments,
    list_conflicts,
    resolve_conflict,
    revert_amendment,
    upsert_amendment_with_side_effects,
)
from raa_api.editorial_batch import apply_batch_changes, fetch_batch_rows
from raa_api.editorial_import import TEMPLATE_FILENAME, build_persoon_template_xlsx, import_persoon_file
from raa_api.schemas import AmendmentCreate, BatchAmendmentRequest, ConflictResolve, SearchRequest
from raa_api.search import (
    browse_az,
    get_functie_detail,
    get_instelling_detail,
    get_persoon_detail,
    list_periods,
    list_stands,
    search_aanstellingen,
    search_functies,
    search_instellingen,
    search_personen,
    summarize_aanstellingen,
    summarize_personen,
    suggest_field,
)

STATIC = Path(__file__).resolve().parents[2] / "frontend" / "static"

_ADMIN_ORIGINS = list(editorial_settings().cors_origins)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if editorial_settings().enabled:
        from raa_api.db import SessionLocal

        db = SessionLocal()
        try:
            ensure_editorial_schema(db)
        finally:
            db.close()
    yield


app = FastAPI(title="RAA Modernized API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ADMIN_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

if STATIC.exists():
    app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    index_file = STATIC / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "RAA API running; add web/frontend/static/index.html"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/periods")
def api_periods(context: str = "personen", db: Session = Depends(get_db)):
    return list_periods(db, context)


@app.get("/api/stands")
def api_stands(db: Session = Depends(get_db)):
    return list_stands(db)


@app.post("/api/search/personen")
def api_search_personen(req: SearchRequest, db: Session = Depends(get_db)):
    return search_personen(db, req)


@app.post("/api/search/personen/summary")
def api_summarize_personen(req: SearchRequest, db: Session = Depends(get_db)):
    return summarize_personen(db, req)


@app.post("/api/search/aanstellingen")
def api_search_aanstellingen(req: SearchRequest, db: Session = Depends(get_db)):
    return search_aanstellingen(db, req)


@app.post("/api/search/aanstellingen/summary")
def api_summarize_aanstellingen(req: SearchRequest, db: Session = Depends(get_db)):
    return summarize_aanstellingen(db, req)


@app.post("/api/search/instellingen")
def api_search_instellingen(req: SearchRequest, db: Session = Depends(get_db)):
    return search_instellingen(db, req)


@app.post("/api/search/functies")
def api_search_functies(req: SearchRequest, db: Session = Depends(get_db)):
    return search_functies(db, req)


@app.get("/api/personen/{person_id}")
def api_persoon_detail(person_id: int, db: Session = Depends(get_db)):
    detail = get_persoon_detail(db, person_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Persoon niet gevonden")
    return detail


@app.get("/api/instellingen/{instelling_id}")
def api_instelling_detail(instelling_id: int, db: Session = Depends(get_db)):
    detail = get_instelling_detail(db, instelling_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Instelling niet gevonden")
    return detail


@app.get("/api/functies/{functie_id}")
def api_functie_detail(functie_id: int, db: Session = Depends(get_db)):
    detail = get_functie_detail(db, functie_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Functie niet gevonden")
    return detail


@app.get("/api/suggest/{field}")
def api_suggest(
    field: str,
    q: str = "",
    period: str | None = None,
    period_mode: str = "scoped",
    db: Session = Depends(get_db),
):
    return suggest_field(db, field, q, period, period_mode)


@app.get("/api/browse/{entity}/az")
def api_browse_az(
    entity: str,
    letter: str | None = None,
    period: str | None = None,
    period_mode: str = "scoped",
    from_: int = Query(0, alias="from", ge=0),
    size: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if entity not in {"personen", "instellingen", "functies"}:
        raise HTTPException(status_code=404, detail="Onbekende browse-entiteit")
    try:
        return browse_az(
            db,
            entity,
            letter=letter,
            period=period,
            period_mode=period_mode,
            from_=from_,
            size=size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/editorial/amendments")
def api_list_amendments(
    entity_type: str | None = None,
    entity_id: int | None = None,
    status: str = "active",
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    return list_amendments(
        db, entity_type=entity_type, entity_id=entity_id, status=status, limit=limit
    )


@app.post("/api/editorial/amendments")
def api_upsert_amendment(
    body: AmendmentCreate,
    db: Session = Depends(get_db),
    editor_id: str = Depends(require_editor),
):
    if not entity_exists(db, body.entity_type, body.entity_id):
        raise HTTPException(status_code=404, detail=f"{body.entity_type} niet gevonden")
    try:
        row = upsert_amendment_with_side_effects(
            db,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            field=body.field,
            value=body.value,
            editor_id=editor_id,
            note=body.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return row


@app.delete("/api/editorial/amendments/{amendment_id}")
def api_revert_amendment(
    amendment_id: int,
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    row = revert_amendment(db, amendment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Amendment niet gevonden")
    return row


@app.get("/api/editorial/instellingen/{instelling_id}/toelichting")
def api_editorial_instelling_toelichting(
    instelling_id: int,
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    ctx = get_instelling_toelichting_edit_context(db, instelling_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Instelling niet gevonden")
    return ctx


@app.get("/api/editorial/batch/{entity_type}")
def api_editorial_batch_fetch(
    entity_type: str,
    ids: str = Query(..., description="Comma-separated entity ids"),
    fields: str | None = Query(None, description="Comma-separated fields (grid subset)"),
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    raw_ids = [part.strip() for part in ids.split(",") if part.strip()]
    if not raw_ids:
        raise HTTPException(status_code=400, detail="ids is required")
    if len(raw_ids) > 200:
        raise HTTPException(status_code=400, detail="Max 200 ids per request")
    try:
        entity_ids = [int(x) for x in raw_ids]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="ids must be integers") from exc
    field_list = [f.strip() for f in fields.split(",") if f.strip()] if fields else None
    try:
        return fetch_batch_rows(db, entity_type, entity_ids, fields=field_list)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/editorial/amendments/batch")
def api_batch_amendments(
    body: BatchAmendmentRequest,
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    editor_id: str = Depends(require_editor),
):
    if not body.changes:
        raise HTTPException(status_code=400, detail="No changes")
    if len(body.changes) > 500:
        raise HTTPException(status_code=400, detail="Max 500 changes per request")
    result = apply_batch_changes(
        db,
        changes=[c.model_dump() for c in body.changes],
        editor_id=editor_id,
        note=body.note,
        dry_run=dry_run,
    )
    return result


@app.get("/api/editorial/import/persoon/template.xlsx")
def api_import_persoon_template(
    ids: str | None = Query(None, description="Comma-separated persoon ids to prefill"),
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    entity_ids: list[int] | None = None
    if ids:
        raw = [part.strip() for part in ids.split(",") if part.strip()]
        try:
            entity_ids = [int(x) for x in raw]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="ids must be integers") from exc
        if len(entity_ids) > 500:
            raise HTTPException(status_code=400, detail="Max 500 ids in template")
    content = build_persoon_template_xlsx(db, entity_ids=entity_ids)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{TEMPLATE_FILENAME}"'},
    )


@app.post("/api/editorial/import/persoon")
async def api_import_persoon(
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    note: str | None = Query(None),
    db: Session = Depends(get_db),
    editor_id: str = Depends(require_editor),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Bestandsnaam ontbreekt")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Leeg bestand")
    return import_persoon_file(
        db,
        filename=file.filename,
        data=data,
        editor_id=editor_id,
        note=note,
        dry_run=dry_run,
    )


@app.get("/api/editorial/conflicts")
def api_list_conflicts(
    unresolved_only: bool = True,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    return list_conflicts(db, unresolved_only=unresolved_only, limit=limit)


@app.get("/api/editorial/{entity_type}/{entity_id}")
def api_editorial_entity_context(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    ctx = get_entity_edit_context(db, entity_type, entity_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Entiteit niet gevonden")
    return ctx


@app.post("/api/editorial/conflicts/{conflict_id}/resolve")
def api_resolve_conflict(
    conflict_id: int,
    body: ConflictResolve,
    db: Session = Depends(get_db),
    _editor: str = Depends(require_editor),
):
    try:
        row = resolve_conflict(db, conflict_id, body.resolution)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Conflict niet gevonden")
    return row
