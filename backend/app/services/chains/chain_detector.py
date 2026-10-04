"""Operational domino detection — deterministic recurring ordered pairs.

A candidate link A→B exists when B's start is after A's start within a
configured window. Ordering uses start-event observed_at (detection
wall-clock would collapse replay windows). Same-vehicle pairs are excluded
(self-link guard). Groups by (routeA, typeA, routeB, typeB) signature;
strength from occurrence count — NEVER causal confidence, NEVER LLM-scored.
"""
from __future__ import annotations
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.db.models.investigation import Evidence, Investigation
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern
from backend.app.db.models.transit_event import TransitEvent

log = get_logger("chain_detector")

RELATIONSHIP = "MAY_CONTRIBUTE_TO"
ALSO = "TEMPORALLY_ASSOCIATED_WITH"


def strength_of(count: int) -> str:
    if count >= 4:
        return "STRONG_RECURRING"
    if count >= 2:
        return "RECURRING"
    return "OBSERVED_ONCE"


def _start_time(db: Session, nm: NearMiss):
    if not nm.start_event_id:
        return None
    e = db.get(TransitEvent, nm.start_event_id)
    return e.observed_at if e else None


def candidate_pairs(db: Session, agency_id: str, since=None, until=None,
                    window_minutes: int | None = None) -> list[dict]:
    window = window_minutes if window_minutes is not None else settings.CHAIN_WINDOW_MINUTES
    q = db.query(NearMiss).filter_by(agency_id=agency_id).filter(NearMiss.status != "DISMISSED")
    nms = q.all()
    starts = {n.id: _start_time(db, n) for n in nms}
    nms = [n for n in nms if starts[n.id] is not None]
    def _norm(dt):
        return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt
    if since:
        since = _norm(since)
        nms = [n for n in nms if _norm(starts[n.id]) >= since]
    if until:
        until = _norm(until)
        nms = [n for n in nms if _norm(starts[n.id]) < until]
    nms.sort(key=lambda n: starts[n.id])
    pairs = []
    for i, a in enumerate(nms):
        for b in nms[i + 1:]:
            gap = (starts[b.id] - starts[a.id]).total_seconds() / 60.0
            if gap <= 0:
                continue
            if gap > window:
                break  # sorted: later b only wider
            if a.vehicle_id and a.vehicle_id == b.vehicle_id:
                continue
            pairs.append({"a": a, "b": b, "gap_minutes": round(gap, 1)})
    return pairs


def evidence_for_nm(db: Session, near_miss_id: str) -> list[str]:
    """Evidence row ids citing a near-miss across any investigation (agency-agnostic)."""
    return [e.id for e in db.query(Evidence).filter_by(
        source_entity_type="near_miss", source_entity_id=near_miss_id).all()]


def _member_evidence_ids(db: Session, pattern_id: str) -> dict[str, list[str]]:
    """Map near-miss id → its Evidence row ids within this pattern's investigations."""
    inv_ids = [i.id for i in db.query(Investigation).filter_by(pattern_id=pattern_id).all()]
    out: dict[str, list[str]] = defaultdict(list)
    if not inv_ids:
        return out
    for e in db.query(Evidence).filter(Evidence.investigation_id.in_(inv_ids)).all():
        if e.source_entity_type == "near_miss":
            out[e.source_entity_id].append(e.id)
    return out


def detect_chains(db: Session, agency_id: str, since=None, until=None,
                  window_minutes: int | None = None,
                  member_ids: set[str] | None = None) -> list[dict]:
    """Group candidate pairs by signature. If member_ids given, keep pairs whose
    source A is a member (pattern-scoped view). Stateless: reruns are identical."""
    pairs = candidate_pairs(db, agency_id, since, until, window_minutes)
    groups: dict[tuple, list] = defaultdict(list)
    for p in pairs:
        a, b = p["a"], p["b"]
        if member_ids is not None and a.id not in member_ids:
            continue
        key = (a.route_id, a.near_miss_type, b.route_id, b.near_miss_type)
        groups[key].append(p)
    chains = []
    for (ra, ta, rb, tb), occs in groups.items():
        occs.sort(key=lambda o: o["gap_minutes"])
        gaps = [o["gap_minutes"] for o in occs]
        chains.append({
            "key": f"{ra or 'noroute'}|{ta}|{rb or 'noroute'}|{tb}",
            "source_route_id": ra, "source_type": ta,
            "target_route_id": rb, "target_type": tb,
            "relationship": RELATIONSHIP, "also": ALSO,
            "strength": strength_of(len(occs)),
            "occurrences": len(occs),
            "avg_gap_minutes": round(sum(gaps) / len(gaps), 1),
            "pairs": [{"a_id": o["a"].id, "b_id": o["b"].id,
                       "a_at": _start_time(db, o["a"]).isoformat(),
                       "b_at": _start_time(db, o["b"]).isoformat(),
                       "gap_minutes": o["gap_minutes"]} for o in occs],
        })
    chains.sort(key=lambda c: (-c["occurrences"], c["avg_gap_minutes"]))
    return chains


def pattern_chains(db: Session, pattern_id: str, since=None, until=None,
                   window_minutes: int | None = None) -> tuple[list[dict], dict]:
    from backend.app.db.models.pattern import Pattern
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        from backend.app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError(f"pattern {pattern_id} not found")
    links = db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all()
    member_ids = {ln.near_miss_id for ln in links}
    chains = detect_chains(db, pattern.agency_id, since, until, window_minutes, member_ids)
    evmap = _member_evidence_ids(db, pattern_id)
    for c in chains:
        ids: list[str] = []
        for pr in c["pairs"]:
            ids.extend(evmap.get(pr["a_id"], []))
            ids.extend(evmap.get(pr["b_id"], []))
        # dedupe, cap
        seen, out = set(), []
        for i in ids:
            if i not in seen:
                seen.add(i)
                out.append(i)
        c["evidence_ids"] = out[:20]
    log.info(f"chains_detected pattern={pattern_id} n={len(chains)}")
    return chains, {"pattern_id": pattern_id}
