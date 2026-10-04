"""Resilience Radar — per-route operational stress prioritization.

Heuristic composite indicator (weights documented, not calibrated, not
learned). Missing signals redistribute weight; zero history yields
INSUFFICIENT_DATA (absence of incidents is not resilience). Language:
operational resilience indicator — never safety/accident/failure-probability.
"""
from __future__ import annotations
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.db.models.route import Route
from backend.app.services.chains.chain_detector import candidate_pairs

WEIGHTS = {"frequency": 25, "recurrence": 20, "peak": 20,
           "recovery": 15, "chain": 10, "trend": 10}


def _cap(x: float, cap: float) -> float:
    return min(max(x, 0.0) / cap, 1.0) * 100.0


def _naive(dt):
    return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt


def _trend(all_at: list, since, until) -> float | None:
    """Recent-third vs older counts mapped to stress. None if data too thin."""
    pts = [_naive(t) for t in all_at if t]
    if len(pts) < 4 or not since or not until:
        return None
    s, u = _naive(since), _naive(until)
    span = (u - s).total_seconds()
    if span <= 0:
        return None
    from datetime import timedelta
    cut = s + timedelta(seconds=span * 2 / 3)
    recent = sum(1 for t in pts if t >= cut)
    older = len(pts) - recent
    if older == 0:
        return 100.0 if recent else 50.0
    return min((recent / older) / 2.0, 1.0) * 100.0


def route_resilience(db: Session, agency_id: str, route_id: str,
                     since=None, until=None) -> dict:
    route = db.get(Route, route_id)
    ext = (route.short_name or route.long_name or route.external_route_id) if route else route_id
    q = db.query(NearMiss).filter_by(agency_id=agency_id, route_id=route_id)
    q = q.filter(NearMiss.status != "DISMISSED")
    nms = q.all()
    if not nms:
        return {"route_id": route_id, "route": ext, "status": "INSUFFICIENT_DATA",
                "resilience": None, "signals": {}, "samples": {"near_misses": 0}}
    from backend.app.db.models.transit_event import TransitEvent

    def _start(nm):
        e = db.get(TransitEvent, nm.start_event_id) if nm.start_event_id else None
        return e.observed_at if e else None
    starts = [(nm, _start(nm)) for nm in nms]
    if since:
        s = _naive(since)
        starts = [(nm, t) for nm, t in starts if t and _naive(t) >= s]
    if until:
        u = _naive(until)
        starts = [(nm, t) for nm, t in starts if t and _naive(t) < u]
    if not starts:
        return {"route_id": route_id, "route": ext, "status": "INSUFFICIENT_DATA",
                "resilience": None, "signals": {}, "samples": {"near_misses": 0}}
    members = [nm for nm, _ in starts]
    peaks = [(nm.abnormal_value or {}).get("peak_delay") for nm in members]
    peaks = [p for p in peaks if isinstance(p, (int, float))]
    durs = [nm.recovery_duration_seconds for nm in members if nm.recovery_duration_seconds]
    patterns = db.query(Pattern).filter_by(agency_id=agency_id, route_id=route_id).all()
    max_rec = max([p.recurrence_count for p in patterns] + [1])
    chain_occ = 0
    for pr in candidate_pairs(db, agency_id):
        if pr["a"].route_id == route_id or pr["b"].route_id == route_id:
            chain_occ += 1
    signals: dict[str, float | None] = {
        "frequency": _cap(len(members), 10),
        "recurrence": _cap(max_rec, 6),
        "peak": _cap(max(peaks) if peaks else 0, 1200),
        "recovery": _cap(sum(durs) / len(durs), 1800) if durs else None,
        "chain": _cap(chain_occ, 6),
        "trend": _trend([t for _, t in starts if t], since, until),
    }
    avail = {k: v for k, v in signals.items() if v is not None}
    total_w = sum(WEIGHTS[k] for k in avail)
    stress = sum(avail[k] * WEIGHTS[k] / total_w for k in avail)
    resilience = round(max(0.0, min(100.0 - stress, 100.0)), 1)
    status = "OBSERVED_STRESS" if resilience < 40 else ("ELEVATED" if resilience < 70 else "STABLE")
    return {"route_id": route_id, "route": ext, "status": status,
            "resilience": resilience,
            "signals": {k: (round(v, 1) if v is not None else None) for k, v in signals.items()},
            "samples": {"near_misses": len(members)}}


def overview(db: Session, agency_id: str | None = None, since=None, until=None,
             route_id: str | None = None, limit: int = 50) -> list[dict]:
    routes = db.query(Route)
    if route_id:
        routes = routes.filter_by(id=route_id)
    items = []
    for r in routes.all():
        ag = agency_id or r.agency_id
        item = route_resilience(db, ag, r.id, since, until)
        items.append(item)
    items.sort(key=lambda d: (d["resilience"] is None, d["resilience"] if d["resilience"] is not None else 0))
    return items[:max(limit, 1)]
