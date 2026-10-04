"""Grounded recommendations — evidence-linked, no overclaiming ('review', not 'fix')."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.logging import get_logger
from backend.app.db.models.recommendation import Recommendation

log = get_logger("recommendation_service")
ALLOWED_TYPES = {"OBSERVE", "SCHEDULE_REVIEW", "ALERT_REVIEW", "SEGMENT_INSPECTION", "COMPARE_ROUTES", "MODELED_INTERVENTION"}


def create_recommendation(db: Session, investigation_id: str, title: str, description: str,
                          expected_effect: str = "", confidence: float = 0.5,
                          recommendation_type: str = "OBSERVE") -> Recommendation:
    rtype = recommendation_type if recommendation_type in ALLOWED_TYPES else "OBSERVE"
    rec = Recommendation(investigation_id=investigation_id, recommendation_type=rtype, title=title[:500],
                         description=description[:2000],
                         rationale="Grounded in evidence bundle; see investigation evidence.",
                         expected_effect=expected_effect[:1000], confidence_score=confidence, status="PROPOSED")
    db.add(rec)
    db.commit()
    db.refresh(rec)
    log.info(f"recommendation_created id={rec.id}")
    return rec
