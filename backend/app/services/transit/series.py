"""Observed delay-series builder (moved verbatim from api/routes/detail.py;
behavior unchanged). Single source for detail endpoint + counterfactual lab."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.transit_event import TransitEvent


def delay_series_for(db: Session, nm: NearMiss, start: TransitEvent | None,
                     rec: TransitEvent | None) -> list[dict]:
    """Persisted vehicle delay points between start and recovery bounds
    (inclusive), chronological. No interpolation — missing points omitted."""
    if start is None or start.observed_at is None or not nm.vehicle_id:
        return []
    lower = start.observed_at
    upper = rec.observed_at if rec is not None and rec.observed_at is not None else nm.detected_at
    if upper is None or upper < lower:
        return []
    rows = (db.query(TransitEvent)
            .filter(TransitEvent.vehicle_id == nm.vehicle_id,
                    TransitEvent.observed_at >= lower,
                    TransitEvent.observed_at <= upper,
                    TransitEvent.delay_seconds.is_not(None))
            .order_by(TransitEvent.observed_at.asc()).limit(200).all())
    return [{"timestamp": r.observed_at.isoformat() if r.observed_at else None,
             "delay_minutes": round(r.delay_seconds / 60.0, 1)} for r in rows]
