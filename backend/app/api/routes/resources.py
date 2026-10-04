"""Resource routers: full-row reads (contract needs fields, not just IDs)."""
from __future__ import annotations
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.repositories import (AgencyRepository, RouteRepository, StopRepository, VehicleRepository,
                                      EventRepository, NearMissRepository, PatternRepository,
                                      InvestigationRepository, RecommendationRepository,
                                      InterventionRepository, VerificationRepository)

router = APIRouter()
_SKIP = {"raw_payload", "normalized_payload", "metadata", "meta", "payload", "execution_result",
         "baseline_metrics", "post_metrics", "baseline_value", "abnormal_value", "features"}


def serialize(obj) -> dict:
    out = {}
    for attr in obj.__mapper__.column_attrs:
        v = getattr(obj, attr.key)
        if isinstance(v, datetime):
            v = v.isoformat()
        elif isinstance(v, date):
            v = v.isoformat()
        out[attr.key] = v
    return out


def _repo_router(prefix: str, repo_cls, not_found: str, filters: tuple = ()):
    r = APIRouter()

    @r.get(prefix)
    def list_items(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
        q = db.query(repo_cls.model)
        if hasattr(repo_cls.model, "observed_at"):
            q = q.order_by(repo_cls.model.observed_at.desc())
        elif hasattr(repo_cls.model, "created_at"):
            q = q.order_by(repo_cls.model.created_at.desc())
        return [serialize(o) for o in q.offset(offset).limit(min(max(limit, 1), 200)).all()]

    @r.get(prefix + "/{item_id}")
    def get_item(item_id: str, db: Session = Depends(get_db)):
        obj = repo_cls(db).get(item_id)
        if not obj:
            raise HTTPException(404, not_found)
        d = serialize(obj)
        for extra in ("raw_payload", "normalized_payload", "baseline_value", "abnormal_value",
                      "features", "payload", "baseline_metrics", "post_metrics", "execution_result"):
            if hasattr(obj, extra):
                d[extra] = getattr(obj, extra)
        return d
    return r


for _prefix, _repo, _name in [
    ("/agencies", AgencyRepository, "agency not found"),
    ("/routes", RouteRepository, "route not found"),
    ("/stops", StopRepository, "stop not found"),
    ("/vehicles", VehicleRepository, "vehicle not found"),
    ("/events", EventRepository, "event not found"),
    ("/near-misses", NearMissRepository, "near-miss not found"),
    ("/patterns", PatternRepository, "pattern not found"),
    ("/investigations", InvestigationRepository, "investigation not found"),
    ("/recommendations", RecommendationRepository, "recommendation not found"),
    ("/interventions", InterventionRepository, "intervention not found"),
    ("/verifications", VerificationRepository, "verification not found"),
]:
    router.include_router(_repo_router(_prefix, _repo, _name))
