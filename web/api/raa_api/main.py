from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from raa_api.db import get_db
from raa_api.schemas import SearchRequest
from raa_api.search import (
    get_functie_detail,
    get_instelling_detail,
    get_persoon_detail,
    list_periods,
    search_aanstellingen,
    search_functies,
    search_instellingen,
    search_personen,
    suggest_field,
)

STATIC = Path(__file__).resolve().parents[2] / "frontend" / "static"

app = FastAPI(title="RAA Modernized API", version="0.1.0")

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


@app.post("/api/search/personen")
def api_search_personen(req: SearchRequest, db: Session = Depends(get_db)):
    return search_personen(db, req)


@app.post("/api/search/aanstellingen")
def api_search_aanstellingen(req: SearchRequest, db: Session = Depends(get_db)):
    return search_aanstellingen(db, req)


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
