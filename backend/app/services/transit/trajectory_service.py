"""Recent movement trajectory for a trip/vehicle (last N positions)."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.db.models.transit_event import TransitEvent


def trajectory(db: Session, vehicle_id: str | None = None, trip_id: str | None = None, limit: int = 50) -> list[dict]:
    q = db.query(TransitEvent)
    if vehicle_id:
        q = q.filter_by(vehicle_id=vehicle_id)
    if trip_id:
        q = q.filter_by(trip_id=trip_id)
    rows = q.order_by(TransitEvent.observed_at.desc()).limit(limit).all()
    return [{"at": r.observed_at.isoformat() if r.observed_at else None, "lat": r.latitude,
             "lon": r.longitude, "delay": r.delay_seconds} for r in reversed(rows)]
