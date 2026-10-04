"""State reconstruction: OBSERVED vs DERIVED vs INFERENCE vs COUNTERFACTUAL."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.db.models.transit_event import TransitEvent


def reconstruct_vehicle_state(db: Session, vehicle_id: str, limit: int = 20) -> dict:
    events = (db.query(TransitEvent).filter_by(vehicle_id=vehicle_id)
              .order_by(TransitEvent.observed_at.desc()).limit(limit).all())
    events = list(reversed(events))
    observed = [{"at": e.observed_at.isoformat() if e.observed_at else None, "delay": e.delay_seconds,
                 "lat": e.latitude, "lon": e.longitude, "type": e.event_type} for e in events]
    delays = [e.delay_seconds for e in events if e.delay_seconds is not None]
    derived = {"latest_delay": delays[-1] if delays else None,
               "max_delay": max(delays) if delays else None,
               "n_events": len(events)}
    inference = {"trend": "escalating" if len(delays) >= 3 and delays[-1] > delays[0] else "stable"}
    counterfactual = {"note": "had recovery not occurred, delay may have persisted (not a prediction)"}
    current = events[-1] if events else None
    return {"observed_fact": observed,
            "derived_metric": derived,
            "inference": inference,
            "counterfactual": counterfactual,
            "current": {"route_id": current.route_id if current else None,
                        "trip_id": current.trip_id if current else None,
                        "position": {"lat": current.latitude, "lon": current.longitude} if current else None,
                        "delay": derived["latest_delay"]}}
