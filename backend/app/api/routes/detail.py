"""Chain detail endpoints: pattern → members → investigation → evidence →
recommendation → intervention → verification. Powers frontend slices 3-7."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.api.routes.resources import serialize
from backend.app.db.models.investigation import Evidence, Investigation
from backend.app.db.models.intervention import Intervention
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.db.models.recommendation import Recommendation
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.verification import Verification
from backend.app.services.transit.series import delay_series_for

router = APIRouter()


@router.get("/patterns/{pattern_id}/detail")
def pattern_detail(pattern_id: str, db: Session = Depends(get_db)):
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise HTTPException(404, "pattern not found")
    members = []
    for link in db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all():
        nm = db.get(NearMiss, link.near_miss_id)
        if nm:
            d = serialize(nm)
            start = db.get(TransitEvent, nm.start_event_id) if nm.start_event_id else None
            rec = db.get(TransitEvent, nm.recovery_event_id) if nm.recovery_event_id else None
            d["start_event"] = serialize(start) if start else None
            d["recovery_event"] = serialize(rec) if rec else None
            d["delay_series"] = delay_series_for(db, nm, start, rec)
            members.append(d)
    invs = [serialize(i) for i in db.query(Investigation).filter_by(pattern_id=pattern_id).all()]
    for inv in invs:
        inv["evidence"] = [serialize(e) for e in db.query(Evidence).filter_by(investigation_id=inv["id"]).all()]
        recs = [serialize(r) for r in db.query(Recommendation).filter_by(investigation_id=inv["id"]).all()]
        for rec in recs:
            ivs = [serialize(x) for x in db.query(Intervention).filter_by(recommendation_id=rec["id"]).all()]
            for x in ivs:
                x["verifications"] = [serialize(v) for v in db.query(Verification).filter_by(intervention_id=x["id"]).all()]
            rec["interventions"] = ivs
        inv["recommendations"] = recs
    return {"pattern": serialize(pattern), "members": members, "investigations": invs}
