"""Emerging near-miss forecast — deterministic early-warning heuristic.

Score 0–100 from six weighted signals (weights sum to 100; missing signals
redistribute; <3 available → INSUFFICIENT_DATA). EVERY input filtered to
observed_at <= evaluated_at: no future leakage by construction. Bands
<30 NORMAL / 30–60 WATCH / >60 EMERGING are configured heuristics, not
calibrated probabilities. Language: emerging operational stress only.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.core.exceptions import EntityNotFoundError
from backend.app.core.logging import get_logger
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.db.models.transit_event import TransitEvent
from backend.app.services.chains.chain_detector import evidence_for_nm, pattern_chains
from backend.app.services.fingerprints.engine import fingerprint_for, similar_patterns
from backend.app.services.transit.baseline import median_baseline

log = get_logger("forecast")

WEIGHTS = {"DEVIATION_TREND": 25, "RECOVERY_WEAKENING": 20, "RECURRENCE": 15,
           "FINGERPRINT_SIMILARITY": 15, "CHAIN_EXPOSURE": 15, "RECENT_STRESS": 10}


def _naive(dt):
    return dt.replace(tzinfo=None) if getattr(dt, "tzinfo", None) else dt


def _cap(x: float, cap: float) -> float:
    return min(max(x, 0.0) / cap, 1.0) * 100.0


def _start(db: Session, nm: NearMiss):
    e = db.get(TransitEvent, nm.start_event_id) if nm.start_event_id else None
    return e.observed_at if e else None


def _members_upto(db: Session, pattern_id: str, at) -> list:
    links = db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all()
    out = []
    for ln in links:
        nm = db.get(NearMiss, ln.near_miss_id)
        st = _start(db, nm) if nm else None
        if nm and st and _naive(st) <= _naive(at):
            out.append((nm, st))
    return sorted(out, key=lambda t: t[1])


def _route_events_upto(db: Session, agency_id: str, route_id: str, at) -> list:
    return (db.query(TransitEvent)
            .filter(TransitEvent.agency_id == agency_id, TransitEvent.route_id == route_id,
                    TransitEvent.delay_seconds.is_not(None),
                    TransitEvent.observed_at <= at)
            .order_by(TransitEvent.observed_at.asc()).limit(2000).all())


_FP_CACHE: dict[str, dict] = {}


def _cached_fp(db: Session, pid: str) -> dict:
    if pid not in _FP_CACHE:
        _FP_CACHE[pid] = fingerprint_for(db, pid)
    return _FP_CACHE[pid]


def _sig(name: str, value: float | None, summary: str, evidence: list) -> dict:
    return {"name": name, "available": value is not None,
            "value": round(value, 1) if value is not None else None,
            "contribution": None, "summary": summary, "evidence_ids": evidence[:10]}


def forecast_pattern(db: Session, pattern_id: str, at=None) -> dict:
    at = at or datetime.now(timezone.utc)
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise EntityNotFoundError(f"pattern {pattern_id} not found")
    members = _members_upto(db, pattern_id, at)
    ev: dict[str, list] = {}
    for nm, _ in members:
        ev[nm.id] = evidence_for_nm(db, nm.id)
    alleV = sorted({i for ids in ev.values() for i in ids})
    sigs: list[dict] = []

    # 1. DEVIATION_TREND — recent vs older median delay on route events
    evts = _route_events_upto(db, pattern.agency_id, pattern.route_id, at)
    if len(evts) >= 6:
        ds = [e.delay_seconds for e in evts]
        half = len(ds) // 2
        older, recent = ds[:half], ds[half:]
        base = median_baseline(older)
        spread = max(base["spread"], 60.0)
        trend = (sum(recent) / len(recent) - sum(older) / len(older)) / spread
        score = min(max((trend + 1.0) / 2.0, 0.0), 1.0) * 100.0
        direction = "increasing" if trend > 0.15 else ("decreasing" if trend < -0.15 else "stable")
        sigs.append(_sig("DEVIATION_TREND", score, f"Recent deviation is {direction} vs baseline", alleV))
    else:
        sigs.append(_sig("DEVIATION_TREND", None, "Fewer than 6 delay observations", []))

    # 2. RECOVERY_WEAKENING — recent vs historical avg recovery duration
    durs = [nm.recovery_duration_seconds for nm, _ in members
            if nm.recovery_duration_seconds]
    if len(durs) >= 3:
        half = max(len(durs) // 2, 1)
        hist, rec = durs[:-half], durs[-half:]
        hav = sum(hist) / len(hist)
        rav = sum(rec) / len(rec)
        weaken = (rav / hav - 1.0) if hav > 0 else 0.0
        score = min(max(weaken, 0.0), 1.0) * 100.0
        state = "weaker than historical behavior" if weaken > 0.1 else "stable vs history"
        sigs.append(_sig("RECOVERY_WEAKENING", score, f"Recovery is {state}", alleV))
    else:
        sigs.append(_sig("RECOVERY_WEAKENING", None, "Fewer than 3 recovery observations", []))

    # 3. RECURRENCE
    sigs.append(_sig("RECURRENCE", _cap(len(members), 6),
                     f"{len(members)} historical near-misses in scope", alleV))

    # 4. FINGERPRINT_SIMILARITY — max similarity to other patterns known by `at`
    try:
        others = [p for p in db.query(Pattern).all()
                  if p.id != pattern_id and p.first_seen_at and _naive(p.first_seen_at) <= _naive(at)]
        if others:
            base = _cached_fp(db, pattern_id)
            from backend.app.services.fingerprints.engine import similarity
            best, matched = 0.0, []
            for p in others[:5]:
                try:
                    s, m = similarity(base, _cached_fp(db, p.id))
                except EntityNotFoundError:
                    continue
                if s > best:
                    best, matched = s, m
            sigs.append(_sig("FINGERPRINT_SIMILARITY", best,
                             f"Current pattern resembles a known fingerprint ({', '.join(matched) or 'weak overlap'})", alleV))
        else:
            sigs.append(_sig("FINGERPRINT_SIMILARITY", None, "No other patterns to compare", []))
    except EntityNotFoundError:
        sigs.append(_sig("FINGERPRINT_SIMILARITY", None, "Fingerprint unavailable", []))

    # 5. CHAIN_EXPOSURE — recurring temporal sequence involvement up to `at`
    chains, _ = pattern_chains(db, pattern_id, until=at)
    occ = sum(c["occurrences"] for c in chains)
    sigs.append(_sig("CHAIN_EXPOSURE", _cap(occ, 6),
                     f"Recurring temporal exposure in {occ} chain occurrences", alleV))

    # 6. RECENT_STRESS — member fraction in the most recent quarter of scope
    if len(members) >= 2:
        t0 = _naive(members[0][1])
        span = (_naive(at) - t0).total_seconds()
        if span > 0:
            cut = t0.timestamp() + span * 3 / 4
            import datetime as _dt
            recent = sum(1 for _, st in members if _naive(st).timestamp() >= cut)
            sigs.append(_sig("RECENT_STRESS", recent / len(members) * 100.0,
                             f"{recent} of {len(members)} near-misses in the recent quarter", alleV))
        else:
            sigs.append(_sig("RECENT_STRESS", None, "No time span in scope", []))
    else:
        sigs.append(_sig("RECENT_STRESS", None, "Fewer than 2 near-misses in scope", []))

    avail = [s for s in sigs if s["available"]]
    if not members or len(avail) < 3:
        return {"pattern_id": pattern_id, "evaluated_at": at.isoformat(),
                "score": None, "status": "INSUFFICIENT_DATA", "signals": sigs,
                "evidence_ids": alleV[:20],
                "note": "Insufficient history for a meaningful assessment."}
    total_w = sum(WEIGHTS[s["name"]] for s in avail)
    for s in avail:
        s["contribution"] = round(s["value"] * WEIGHTS[s["name"]] / total_w, 1)
    score = round(sum(s["contribution"] for s in avail), 1)
    status = "EMERGING" if score > 60 else ("WATCH" if score >= 30 else "NORMAL")
    log.info(f"forecast pattern={pattern_id} score={score} status={status}")
    return {"pattern_id": pattern_id, "evaluated_at": at.isoformat(),
            "score": score, "status": status, "signals": sigs,
            "evidence_ids": alleV[:20],
            "note": "Operational early-warning signal, not a guaranteed prediction. "
                    "Bands 30/60 are configured heuristics."}
