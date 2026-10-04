"""Near-miss detector: NORMAL → DEVIATION → ESCALATION → RECOVERY (no failure).
A plain 'delay > X' is NOT a near-miss. Requires all four:
1. abnormal state (delay ≥ threshold), 2. deviation from baseline,
3. recovery before cancellation/failure, 4. operational significance.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.transit_event import TransitEvent
from backend.app.services.detection.recovery_detector import detect_recovery
from backend.app.services.detection.confidence import confidence as conf_score
from backend.app.services.transit.baseline import median_baseline, is_deviation

log = get_logger("near_miss_detector")


def detect_for_vehicle(db: Session, vehicle_id: str, agency_id: str, window: int = 12) -> NearMiss | None:
    events = (db.query(TransitEvent).filter_by(vehicle_id=vehicle_id)
              .order_by(TransitEvent.observed_at.desc()).limit(window).all())
    events = list(reversed(events))
    series = [(e.observed_at, e.delay_seconds) for e in events if e.delay_seconds is not None]
    if len(series) < 4:
        return None
    # exclude cancelled trips (full failure → not a near-miss)
    if any(e.event_type == "CANCELLATION" for e in events):
        return None
    delays = [d for _, d in series]
    # Baseline from pre-escalation points (normal state), NOT the event window
    # itself (which would inflate the median and mask the deviation).
    early = [d for d in delays[:3] if d < settings.NEAR_MISS_THRESHOLD] or delays[:2] or [delays[0]]
    baseline = median_baseline(early)
    peak = max(delays)
    if peak < settings.NEAR_MISS_THRESHOLD:
        return None
    if not is_deviation(peak, baseline, settings.DEVIATION_SIGMA, settings.NEAR_MISS_THRESHOLD):
        return None
    rec = detect_recovery(series, settings.NEAR_MISS_THRESHOLD, settings.RECOVERY_THRESHOLD)
    if not rec:
        return None
    # idempotency: same start event → reuse
    start_event = events[0]
    existing = db.query(NearMiss).filter_by(start_event_id=start_event.id).first()
    if existing:
        return existing
    nm = NearMiss(
        agency_id=agency_id, route_id=events[-1].route_id, trip_id=events[-1].trip_id,
        vehicle_id=vehicle_id, start_event_id=start_event.id, recovery_event_id=events[-1].id,
        detected_at=datetime.now(timezone.utc), near_miss_type="DELAY_SPIKE_RECOVERY",
        severity="HIGH" if peak >= settings.NEAR_MISS_THRESHOLD * 1.5 else "MEDIUM",
        baseline_value=baseline,
        abnormal_value={"peak_delay": peak, "final_delay": rec["final"]},
        recovery_duration_seconds=rec["recovery_duration_seconds"] or 0,
        confidence_score=conf_score(len(series), peak, settings.NEAR_MISS_THRESHOLD),
        status="DETECTED",
        detection_reason=f"Peak delay {peak}s deviated from baseline median {baseline['median']:.0f}s and recovered to {rec['final']}s.")
    db.add(nm)
    db.commit()
    db.refresh(nm)
    log.info(f"near_miss_detected id={nm.id} peak={peak}")
    return nm
