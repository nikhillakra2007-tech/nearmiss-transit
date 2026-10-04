"""Orchestrator: build bundle → provider → validate → persist summary/recommendation."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.logging import get_logger
from backend.app.db.models.investigation import Evidence
from backend.app.db.models.pattern import Pattern
from backend.app.services.agent import tools as T
from backend.app.services.agent.planner import validate_agent_output
from backend.app.services.agent.provider import get_provider
from backend.app.services.investigation.investigator import complete_investigation
from backend.app.services.recommendations.recommendation_service import create_recommendation

log = get_logger("orchestrator")


def investigate_with_agent(db: Session, investigation_id: str, pattern_id: str) -> dict:
    from backend.app.db.models.investigation import Investigation
    inv = db.get(Investigation, investigation_id)
    pattern = db.get(Pattern, pattern_id)
    evs = db.query(Evidence).filter_by(investigation_id=investigation_id).all()
    bundle = {"pattern": T.get_pattern(db, pattern_id),
              "near_misses": T.get_near_misses(db, pattern_id),
              "timeline": T.get_event_timeline(db, pattern_id),
              "alerts": T.get_service_alerts(db, pattern.route_id if pattern else None),
              "baseline": T.get_baseline(db, pattern_id),
              "evidence": [{"id": e.id, "type": e.evidence_type, "description": e.description} for e in evs]}
    provider = get_provider()
    raw = provider.generate(bundle)
    valid_ids = {e.id for e in evs}
    validated = validate_agent_output(raw, valid_ids)
    summary = validated["summary"]
    complete_investigation(db, investigation_id, summary, validated["claims"][0]["confidence"] if validated["claims"] else 0.5)
    rec = validated["recommendation"]
    recommendation = create_recommendation(db, investigation_id, title=rec["title"],
                                           description=rec["description"],
                                           expected_effect=rec.get("expected_effect", ""),
                                           confidence=float(rec.get("confidence", 0.5)))
    log.info(f"recommendation_created id={recommendation.id}")
    return {"investigation_id": investigation_id, "summary": summary, "recommendation_id": recommendation.id}
