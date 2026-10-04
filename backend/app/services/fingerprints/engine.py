"""Operational fingerprints — deterministic pattern signatures + similarity.

Centralized buckets (no magic numbers elsewhere). Similarity weights are
configured constants, not learned. Output language: OPERATIONAL SIGNATURE
SIMILARITY — never root cause, never confidence.
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.exceptions import EntityNotFoundError
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.db.models.route import Route
from backend.app.services.chains.chain_detector import pattern_chains
from backend.app.services.chains.chain_detector import strength_of

WEIGHTS = {"route": 20, "type": 20, "time": 15, "peak": 15, "recovery": 15,
           "recurrence": 10, "chain": 5}


def time_bucket(hour: int | None) -> str:
    if hour is None:
        return "UNKNOWN"
    if hour < 5:
        return "NIGHT"
    if hour < 11:
        return "MORNING"
    if hour < 16:
        return "MIDDAY"
    if hour < 21:
        return "EVENING"
    return "LATE"


def peak_bucket(peak_minutes: float | None) -> str:
    if peak_minutes is None:
        return "UNKNOWN"
    if peak_minutes < 5:
        return "LOW"
    if peak_minutes <= 10:
        return "MODERATE"
    if peak_minutes <= 20:
        return "HIGH"
    return "EXTREME"


def recovery_bucket(avg_seconds: float | None) -> str:
    if avg_seconds is None:
        return "UNKNOWN"
    minutes = avg_seconds / 60.0
    if minutes < 5:
        return "FAST"
    if minutes <= 10:
        return "MODERATE"
    return "SLOW"


def _route_ext(db: Session, route_id: str | None) -> str:
    if not route_id:
        return "UNKNOWN"
    r = db.get(Route, route_id)
    return (r.short_name or r.long_name or r.external_route_id) if r else "UNKNOWN"


def fingerprint_for(db: Session, pattern_id: str) -> dict:
    pattern = db.get(Pattern, pattern_id)
    if not pattern:
        raise EntityNotFoundError(f"pattern {pattern_id} not found")
    links = db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all()
    members = [db.get(NearMiss, ln.near_miss_id) for ln in links]
    members = [m for m in members if m]
    peaks = [(m.abnormal_value or {}).get("peak_delay") for m in members]
    peaks = [p / 60.0 for p in peaks if isinstance(p, (int, float))]
    durs = [m.recovery_duration_seconds for m in members if m.recovery_duration_seconds]
    hour = pattern.first_seen_at.hour if pattern.first_seen_at else None
    peak_b = peak_bucket(max(peaks) if peaks else None)
    rec_b = recovery_bucket(sum(durs) / len(durs) if durs else None)
    rec_strength = strength_of(len(members)) if members else "OBSERVED_ONCE"
    chains, _ = pattern_chains(db, pattern_id)
    chain = bool(chains)
    fp = {"pattern_id": pattern_id,
          "route": _route_ext(db, pattern.route_id),
          "time_bucket": time_bucket(hour),
          "type": pattern.pattern_type,
          "peak_bucket": peak_b,
          "recovery_bucket": rec_b,
          "recurrence_strength": rec_strength,
          "chain_exposure": chain}
    fp["canonical_id"] = "|".join([fp["route"], fp["time_bucket"], fp["type"], peak_b,
                                   rec_b, rec_strength, "CHAIN" if chain else "NOCHAIN"])
    return fp


FIELD_MAP = {"route": "route", "type": "type", "time": "time_bucket",
             "peak": "peak_bucket", "recovery": "recovery_bucket",
             "recurrence": "recurrence_strength", "chain": "chain_exposure"}


def similarity(a: dict, b: dict) -> tuple[float, list[str]]:
    matched = []
    score = 0.0
    for field, weight in WEIGHTS.items():
        key = FIELD_MAP[field]
        if a.get(key) is not None and a.get(key) == b.get(key) and a.get(key) != "UNKNOWN":
            score += weight
            matched.append(field)
    return round(score, 1), matched


def classify(score: float) -> str:
    if score >= 80:
        return "HIGH_MATCH"
    if score >= 50:
        return "PARTIAL_MATCH"
    return "LOW_SIMILARITY"


def similar_patterns(db: Session, pattern_id: str, n: int = 5) -> list[dict]:
    base = fingerprint_for(db, pattern_id)
    out = []
    for p in db.query(Pattern).all():
        if p.id == pattern_id:
            continue
        try:
            fp = fingerprint_for(db, p.id)
        except EntityNotFoundError:
            continue
        score, matched = similarity(base, fp)
        out.append({"pattern_id": p.id, "title": p.title, "similarity": score,
                    "match_class": classify(score), "matched": matched,
                    "fingerprint": fp})
    out.sort(key=lambda d: (-d["similarity"], d["pattern_id"]))
    return out[:max(n, 1)]
