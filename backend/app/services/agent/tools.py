"""Agent tools — the ONLY way the agent touches data (no direct DB)."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.service_alert import ServiceAlert
from backend.app.db.models.investigation import Evidence


def get_pattern(db: Session, pattern_id: str) -> dict | None:
    p = db.get(Pattern, pattern_id)
    return {"id": p.id, "title": p.title, "recurrence_count": p.recurrence_count} if p else None


def get_near_misses(db: Session, pattern_id: str) -> list[dict]:
    links = db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all()
    out = []
    for l in links:
        nm = db.get(NearMiss, l.near_miss_id)
        if nm:
            out.append({"id": nm.id, "type": nm.near_miss_type, "peak": (nm.abnormal_value or {}).get("peak_delay")})
    return out


def get_event_timeline(db: Session, pattern_id: str) -> list[dict]:
    out = []
    for nm in [db.get(NearMiss, l.near_miss_id) for l in db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all()]:
        if nm and nm.start_event_id:
            e = db.get(TransitEvent, nm.start_event_id)
            if e:
                out.append({"event_id": e.id, "at": e.observed_at.isoformat() if e.observed_at else None, "delay": e.delay_seconds})
    return sorted(out, key=lambda d: d["at"] or "")


def get_service_alerts(db: Session, route_id: str | None = None) -> list[dict]:
    q = db.query(ServiceAlert)
    if route_id:
        q = q.filter_by(route_id=route_id)
    return [{"id": a.id, "header": a.header} for a in q.limit(25).all()]


def get_baseline(db: Session, pattern_id: str) -> dict:
    return {"method": "median per route/time-bucket", "note": "computed deterministically"}


def get_route_history(db: Session, route_id: str, limit: int = 50) -> list[dict]:
    rows = db.query(TransitEvent).filter_by(route_id=route_id).order_by(TransitEvent.observed_at.desc()).limit(limit).all()
    return [{"id": r.id, "delay": r.delay_seconds} for r in rows]


def get_stop_history(db: Session, stop_id: str, limit: int = 50) -> list[dict]:
    rows = db.query(TransitEvent).filter_by(stop_id=stop_id).order_by(TransitEvent.observed_at.desc()).limit(limit).all()
    return [{"id": r.id, "delay": r.delay_seconds} for r in rows]


def compare_periods(before: dict, after: dict) -> dict:
    b, a = before.get("avg_delay", 0), after.get("avg_delay", 0)
    return {"delta": a - b, "improved": a < b}
