"""Historical early-warning replay — reuses the deterministic forecast engine.

For a pattern's latest historical near-miss (the target), evaluate
forecast_pattern at earlier cutoffs across a lookback window. EVERY cutoff
passes only its own timestamp to forecast_pattern, which filters all
inputs to observed_at <= cutoff by construction: future observations can
never influence an earlier replay point. No weights/bands are duplicated
here; bands are read verbatim from each forecast result's status.

Language: historical replay using observed data. Not a claim of future
prediction accuracy; the system did not predict the recorded near-miss.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.app.core.exceptions import EntityNotFoundError
from backend.app.core.logging import get_logger
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.db.models.transit_event import TransitEvent
from backend.app.services.forecast.engine import forecast_pattern

log = get_logger("replay")

MODE = "HISTORICAL_REPLAY"
DEFAULT_LOOKBACK_MINUTES = 60
DEFAULT_STEP_MINUTES = 15
MAX_LOOKBACK_MINUTES = 180
MIN_STEP_MINUTES = 5

DISCLAIMER = ("Historical replay using observed data up to each cutoff. "
              "Not a claim of future prediction accuracy. NearMiss Transit "
              "did not predict this recorded near-miss; the replay shows "
              "when its deterministic forecast entered WATCH or EMERGING "
              "before the event.")

_WATCH_BANDS = ("WATCH", "EMERGING")


def _naive(dt):
    return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt


def _member_starts(db: Session, pattern_id: str, end) -> list[tuple]:
    """(near_miss, start_observed_at) with start <= end, oldest first."""
    out = []
    for link in db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all():
        nm = db.get(NearMiss, link.near_miss_id)
        if not nm:
            continue
        start = None
        if nm.start_event_id:
            ev = db.get(TransitEvent, nm.start_event_id)
            start = ev.observed_at if ev is not None else None
        start = start or nm.detected_at
        if start is not None and _naive(start) <= _naive(end):
            out.append((nm, start))
    return sorted(out, key=lambda t: t[1])


def _cutoffs(target, lookback_minutes: int, step_minutes: int) -> list:
    start = target - timedelta(minutes=lookback_minutes)
    points = []
    cur = start
    while _naive(cur) < _naive(target):
        points.append(cur)
        cur = cur + timedelta(minutes=step_minutes)
    points.append(target)
    seen, ordered = set(), []
    for p in points:
        key = _naive(p).isoformat()
        if key not in seen:
            seen.add(key)
            ordered.append(p)
    return ordered


def _trim_signals(signals: list[dict]) -> list[dict]:
    return [{"name": s.get("name"), "available": s.get("available"),
             "value": s.get("value"), "contribution": s.get("contribution"),
             "summary": s.get("summary")} for s in signals]


def _transition(point: dict | None) -> dict | None:
    if not point:
        return None
    return {"cutoff": point["cutoff"],
            "minutes_before_target": point["minutes_before_target"],
            "score": point["score"], "band": point["band"]}


def replay_early_warning(db: Session, pattern_id: str, at=None,
                         lookback_minutes: int = DEFAULT_LOOKBACK_MINUTES,
                         step_minutes: int = DEFAULT_STEP_MINUTES) -> dict:
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise EntityNotFoundError(f"pattern {pattern_id} not found")
    end = at or datetime.now(timezone.utc)
    members = _member_starts(db, pattern_id, end)
    if not members:
        return {"mode": MODE, "pattern_id": pattern_id,
                "status": "INSUFFICIENT_DATA",
                "target_near_miss_id": None, "target_timestamp": None,
                "lookback_minutes": lookback_minutes,
                "step_minutes": step_minutes, "timeline": [],
                "first_watch": None, "first_emerging": None,
                "available_history": {"members_in_scope": 0,
                                      "route_events_in_scope": 0,
                                      "cutoffs_evaluated": 0},
                "disclaimer": DISCLAIMER,
                "note": "Insufficient history for a historical replay: no "
                        "recorded near-miss in scope before the cutoff."}
    target_nm, target_ts = members[-1]
    route_events = (db.query(TransitEvent)
                    .filter(TransitEvent.agency_id == pattern.agency_id,
                            TransitEvent.route_id == pattern.route_id,
                            TransitEvent.delay_seconds.is_not(None),
                            TransitEvent.observed_at <= target_ts)
                    .count())
    timeline = []
    for cutoff in _cutoffs(target_ts, lookback_minutes, step_minutes):
        # No-leakage boundary: only observed_at <= cutoff reaches scoring.
        fc = forecast_pattern(db, pattern_id, at=cutoff)
        mins = round((_naive(target_ts) - _naive(cutoff)).total_seconds() / 60.0, 1)
        timeline.append({
            "cutoff": cutoff.isoformat() if hasattr(cutoff, "isoformat") else str(cutoff),
            "minutes_before_target": mins,
            "score": fc.get("score"),
            "band": fc.get("status"),
            "signals_available": sum(1 for s in fc.get("signals", []) if s.get("available")),
            "signals_total": len(fc.get("signals", [])),
            "signals": _trim_signals(fc.get("signals", []))})
    first_watch = next((p for p in timeline if p["band"] in _WATCH_BANDS), None)
    first_emerging = next((p for p in timeline if p["band"] == "EMERGING"), None)
    scored = sum(1 for p in timeline if p["score"] is not None)
    log.info(f"replay pattern={pattern_id} points={len(timeline)} "
             f"first_watch={bool(first_watch)} first_emerging={bool(first_emerging)}")
    return {"mode": MODE, "pattern_id": pattern_id,
            "status": "COMPLETE" if scored else "INSUFFICIENT_DATA",
            "target_near_miss_id": target_nm.id,
            "target_timestamp": target_ts.isoformat() if hasattr(target_ts, "isoformat") else str(target_ts),
            "lookback_minutes": lookback_minutes, "step_minutes": step_minutes,
            "timeline": timeline,
            "first_watch": _transition(first_watch),
            "first_emerging": _transition(first_emerging),
            "available_history": {"members_in_scope": len(members),
                                  "route_events_in_scope": route_events,
                                  "cutoffs_evaluated": len(timeline)},
            "disclaimer": DISCLAIMER,
            "note": "Historical replay shows when the deterministic forecast "
                    "entered WATCH or EMERGING before the recorded near-miss."}
