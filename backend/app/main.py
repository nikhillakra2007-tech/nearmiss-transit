"""FastAPI entrypoint — modular monolith, /api/v1, typed errors, no stack leaks."""
from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.routes import health, resources, detail, chains, v22
from backend.app.api.deps import get_db
from backend.app.core.config import settings
from backend.app.core.exceptions import NearMissError
from backend.app.core.logging import get_logger, setup_logging
from backend.app.core.security import ALLOWED_ORIGINS
from backend.app.db import session as session_mod
from backend.app.db.base import Base
from backend.app.db import models  # noqa: F401 (register models)
from backend.app.services.ingestion.gtfs_client import fetch_feed
from backend.app.services.ingestion.gtfs_parser import parse_feed, parse_fixture_dicts
from backend.app.services.ingestion.normalizer import normalize
from backend.app.services.ingestion.ingestion_service import persist_normalized
from backend.app.services.investigation.investigator import open_investigation
from backend.app.services.interventions.intervention_service import request_intervention

setup_logging(settings.LOG_LEVEL)
log = get_logger("main")

app = FastAPI(title="NearMiss Transit", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(NearMissError)
async def nearmiss_handler(request: Request, exc: NearMissError):
    log.warning(f"app_error code={exc.code}")
    return JSONResponse({"error": exc.code, "message": str(exc)}, status_code=exc.status_code)


@app.on_event("startup")
def _startup():
    engine = session_mod.engine
    Base.metadata.create_all(bind=engine)
    log.info("startup_complete")


app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["health"])
app.include_router(resources.router, prefix=settings.API_V1_PREFIX, tags=["resources"])
app.include_router(detail.router, prefix=settings.API_V1_PREFIX, tags=["detail"])
app.include_router(chains.router, prefix=settings.API_V1_PREFIX, tags=["chains"])
app.include_router(v22.router, prefix=settings.API_V1_PREFIX, tags=["v22"])


class InvestigationIn(BaseModel):
    pattern_id: str


class InterventionIn(BaseModel):
    recommendation_id: str
    intervention_type: str = "OPERATIONAL_REVIEW"
    target: str = ""


class IngestIn(BaseModel):
    agency_external_id: str = "demo-agency"
    demo_rows: list[dict] | None = None


@app.post(f"{settings.API_V1_PREFIX}/investigations")
def create_investigation(body: InvestigationIn):
    db: Session = next(get_db())
    try:
        inv = open_investigation(db, body.pattern_id)
        return {"id": inv.id, "status": inv.status}
    finally:
        db.close()


@app.post(f"{settings.API_V1_PREFIX}/interventions")
def create_intervention(body: InterventionIn):
    db: Session = next(get_db())
    try:
        inv = request_intervention(db, body.recommendation_id, body.intervention_type, body.target)
        return {"id": inv.id, "execution_status": inv.execution_status}
    finally:
        db.close()


@app.post(f"{settings.API_V1_PREFIX}/ingestion/run")
async def run_ingestion(body: IngestIn):
    """Manual single ingestion cycle. Demo/replay rows accepted; live fetch otherwise."""
    db: Session = next(get_db())
    try:
        if body.demo_rows is not None or settings.DEMO_MODE or not settings.GTFS_REALTIME_URL:
            rows = parse_fixture_dicts(body.demo_rows or [])
            mode = "DEMO/REPLAY"
        else:
            raw = await fetch_feed()
            rows = parse_feed(raw)
            mode = "LIVE"
        normalized = [normalize(r, body.agency_external_id) for r in rows]
        result = persist_normalized(db, normalized)
        result["mode"] = mode
        return result
    finally:
        db.close()


@app.get("/")
def root():
    from pathlib import Path
    from fastapi.responses import FileResponse
    index = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"service": "nearmiss-transit", "docs": "/docs", "health": f"{settings.API_V1_PREFIX}/health"}


@app.get("/app.js")
def app_js():
    from pathlib import Path
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).resolve().parents[2] / "frontend" / "app.js")


@app.get("/styles.css")
def styles_css():
    from pathlib import Path
    from fastapi.responses import FileResponse
    return FileResponse(Path(__file__).resolve().parents[2] / "frontend" / "styles.css")
