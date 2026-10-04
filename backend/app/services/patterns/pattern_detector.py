"""Deterministic pattern detector: group near-misses, persist patterns idempotently."""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import Pattern, NearMissPattern
from backend.app.services.patterns.recurrence import recurrence_key

log = get_logger("pattern_detector")


def detect_patterns(db: Session, min_occurrences: int | None = None) -> list[Pattern]:
    min_occ = min_occurrences or settings.PATTERN_MIN_OCCURRENCES
    nms = db.query(NearMiss).filter(NearMiss.status != "DISMISSED").all()
    groups: dict[str, list] = defaultdict(list)
    for nm in nms:
        groups[recurrence_key(nm)].append(nm)
    created: list[Pattern] = []
    for key, members in groups.items():
        if len(members) < min_occ:
            continue
        members.sort(key=lambda m: m.detected_at)
        # idempotency: fingerprint in features
        existing = db.query(Pattern).filter(Pattern.features["fingerprint"].astext == key).first() if False else None
        # portable lookup (sqlite + postgres):
        existing = next((p for p in db.query(Pattern).all() if (p.features or {}).get("fingerprint") == key), None)
        if existing:
            existing.recurrence_count = len(members)
            existing.last_seen_at = members[-1].detected_at
            for m in members:  # V2 fix: link late-arriving members too (was skipped)
                if not db.query(NearMissPattern).filter_by(near_miss_id=m.id, pattern_id=existing.id).first():
                    db.add(NearMissPattern(near_miss_id=m.id, pattern_id=existing.id))
            db.commit()
            created.append(existing)
            continue
        route_id = members[0].route_id
        p = Pattern(agency_id=members[0].agency_id, route_id=route_id,
                    pattern_type="RECURRING_DELAY_INSTABILITY",
                    title=f"Recurring delay instability ({len(members)}x) key={key}",
                    description=f"{len(members)} near-misses share route/time/type bucket {key}.",
                    recurrence_count=len(members), first_seen_at=members[0].detected_at,
                    last_seen_at=members[-1].detected_at, severity="HIGH",
                    confidence_score=min(0.5 + 0.1 * len(members), 0.95), status="OPEN",
                    features={"fingerprint": key})
        db.add(p)
        db.commit()
        db.refresh(p)
        for m in members:
            if not db.query(NearMissPattern).filter_by(near_miss_id=m.id, pattern_id=p.id).first():
                db.add(NearMissPattern(near_miss_id=m.id, pattern_id=p.id))
        db.commit()
        log.info(f"pattern_detected id={p.id} count={len(members)}")
        created.append(p)
    return created
