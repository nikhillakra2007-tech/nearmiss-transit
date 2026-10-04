"""Investigation lifecycle: pattern → OPEN (idempotent) → evidence → agent → COMPLETED."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.core.exceptions import EntityNotFoundError, InvestigationError
from backend.app.core.logging import get_logger
from backend.app.db.models.investigation import Investigation
from backend.app.db.models.pattern import Pattern
from backend.app.services.investigation.evidence_builder import build_evidence
from backend.app.services.investigation.causal_analysis import propose_edges

log = get_logger("investigator")


def open_investigation(db: Session, pattern_id: str) -> Investigation:
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise EntityNotFoundError(f"pattern {pattern_id} not found")
    active = db.query(Investigation).filter_by(pattern_id=pattern_id).filter(Investigation.status.in_(["OPEN", "UNDER_INVESTIGATION"])).first()
    if active:
        return active
    inv = Investigation(pattern_id=pattern_id, status="OPEN", started_at=datetime.now(timezone.utc))
    db.add(inv)
    db.commit()
    db.refresh(inv)
    log.info(f"investigation_started id={inv.id}")
    build_evidence(db, inv.id, pattern_id)
    propose_edges(db, inv.id)
    return inv


def complete_investigation(db: Session, investigation_id: str, summary: str, confidence: float) -> Investigation:
    inv = db.get(Investigation, investigation_id)
    if not inv:
        raise EntityNotFoundError(f"investigation {investigation_id} not found")
    if inv.status == "COMPLETED":
        raise InvestigationError("already completed")
    inv.status = "COMPLETED"
    inv.investigation_summary = summary[:4000]
    inv.confidence_score = confidence
    inv.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inv)
    log.info(f"investigation_completed id={inv.id}")
    return inv
