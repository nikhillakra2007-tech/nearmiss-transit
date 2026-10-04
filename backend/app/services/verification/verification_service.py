"""Verification loop: compare before/after metrics → 4 outcomes. Closes the agent loop."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.core.exceptions import EntityNotFoundError
from backend.app.core.logging import get_logger
from backend.app.db.models.intervention import Intervention
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.near_miss import NearMiss

log = get_logger("verification_service")


def _avg_delay(db: Session, route_id: str | None, start, end) -> dict:
    q = db.query(TransitEvent)
    if route_id:
        q = q.filter_by(route_id=route_id)
    if start:
        q = q.filter(TransitEvent.observed_at >= start)
    if end:
        q = q.filter(TransitEvent.observed_at < end)
    delays = [r.delay_seconds for r in q.all() if r.delay_seconds is not None]
    nm_count = 0
    if route_id and start and end:
        nm_count = db.query(NearMiss).filter(NearMiss.route_id == route_id,
                                             NearMiss.detected_at >= start,
                                             NearMiss.detected_at < end).count()
    return {"avg_delay": sum(delays) / len(delays) if delays else 0.0, "n": len(delays), "near_misses": nm_count}


def verify(db: Session, intervention_id: str, baseline_window: tuple, post_window: tuple,
           min_samples: int = 5) -> object:
    from backend.app.db.models.verification import Verification
    inv = db.get(Intervention, intervention_id)
    if not inv:
        raise EntityNotFoundError(f"intervention {intervention_id} not found")
    from backend.app.db.models.recommendation import Recommendation
    from backend.app.db.models.investigation import Investigation
    from backend.app.db.models.pattern import Pattern
    rec = db.get(Recommendation, inv.recommendation_id)
    route_id = None
    if rec:
        investigation = db.get(Investigation, rec.investigation_id)
        if investigation:
            pattern = db.get(Pattern, investigation.pattern_id)
            route_id = pattern.route_id if pattern else None
    before = _avg_delay(db, route_id, baseline_window[0], baseline_window[1])
    after = _avg_delay(db, route_id, post_window[0], post_window[1])
    if before["n"] < min_samples or after["n"] < min_samples:
        outcome, conf, expl = "INSUFFICIENT_DATA", 0.3, f"Too few samples (before={before['n']}, after={after['n']})."
    else:
        delta = after["avg_delay"] - before["avg_delay"]
        rel = -delta / max(before["avg_delay"], 1)
        if rel >= 0.2:
            outcome, conf = "IMPROVED", 0.75
        elif rel <= -0.2:
            outcome, conf = "WORSENED", 0.7
        else:
            outcome, conf = "NO_SIGNIFICANT_CHANGE", 0.65
        expl = f"avg delay {before['avg_delay']:.0f}s → {after['avg_delay']:.0f}s; near-misses {before['near_misses']} → {after['near_misses']}."
    v = Verification(intervention_id=intervention_id, verification_started_at=datetime.now(timezone.utc),
                     verification_ended_at=datetime.now(timezone.utc), baseline_metrics=before,
                     post_metrics=after, outcome=outcome, confidence_score=conf, explanation=expl)
    db.add(v)
    db.commit()
    db.refresh(v)
    log.info(f"verification_completed id={v.id} outcome={outcome}")
    return v
