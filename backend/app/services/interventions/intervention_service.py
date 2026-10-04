"""InterventionExecutor abstraction — never fake real-world execution.
MVP: PROPOSED → PENDING_EXTERNAL_ACTION (handoff recorded). Real API pluggable.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.core.exceptions import EntityNotFoundError, UnsupportedInterventionError
from backend.app.core.logging import get_logger
from backend.app.db.models.intervention import Intervention
from backend.app.db.models.recommendation import Recommendation

log = get_logger("intervention_service")
ALLOWED_TYPES = {"OPERATIONAL_REVIEW", "OBSERVATION_TASK", "SCHEDULE_REVIEW_REQUEST", "ALERT_FOLLOWUP"}


class InterventionExecutor:
    def execute(self, intervention: Intervention) -> dict:
        # No real transit-agency API exists in MVP → record handoff, do not fake.
        return {"handoff": "recorded", "external": "pending", "note": "No real action API; marked PENDING_EXTERNAL_ACTION."}


def request_intervention(db: Session, recommendation_id: str, intervention_type: str = "OPERATIONAL_REVIEW",
                         target: str = "") -> Intervention:
    rec = db.get(Recommendation, recommendation_id)
    if not rec:
        raise EntityNotFoundError(f"recommendation {recommendation_id} not found")
    if intervention_type not in ALLOWED_TYPES:
        raise UnsupportedInterventionError(f"unsupported: {intervention_type}")
    inv = Intervention(recommendation_id=recommendation_id, intervention_type=intervention_type,
                       target=target[:500], requested_at=datetime.now(timezone.utc),
                       execution_status="PROPOSED")
    db.add(inv)
    db.commit()
    db.refresh(inv)
    result = InterventionExecutor().execute(inv)
    inv.execution_status = "PENDING_EXTERNAL_ACTION"
    inv.execution_result = result
    db.commit()
    db.refresh(inv)
    log.info(f"intervention_requested id={inv.id}")
    return inv
