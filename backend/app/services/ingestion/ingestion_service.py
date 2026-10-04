"""Idempotent ingestion: same feed twice → no duplicate logical events."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.logging import get_logger
from backend.app.db.models.agency import Agency
from backend.app.db.models.route import Route
from backend.app.db.models.trip import Trip
from backend.app.db.models.vehicle import Vehicle
from backend.app.db.models.stop import Stop
from backend.app.db.models.transit_event import TransitEvent
from backend.app.services.ingestion.normalizer import NormalizedTransitEvent

log = get_logger("ingestion_service")


def _get_or_create_agency(db: Session, ext: str) -> Agency:
    a = db.query(Agency).filter_by(external_id=ext).first()
    if not a:
        a = Agency(external_id=ext, name=ext)
        db.add(a)
        db.commit()
        db.refresh(a)
    return a


def _resolve(db: Session, model, filters: dict, create_kwargs: dict):
    obj = db.query(model).filter_by(**filters).first()
    if obj:
        return obj, False
    obj = model(**create_kwargs)
    db.add(obj)
    return obj, True


def persist_normalized(db: Session, events: list[NormalizedTransitEvent]) -> dict:
    ingested = 0
    duplicates = 0
    errors = 0
    for ev in events:
        try:
            agency = _get_or_create_agency(db, ev.agency_external_id)
            exists = db.query(TransitEvent).filter_by(agency_id=agency.id, source_event_id=ev.source_event_id).first()
            if exists:
                duplicates += 1
                continue
            route_id = trip_id = vehicle_id = stop_id = None
            if ev.route_external_id:
                r, _ = _resolve(db, Route, {"agency_id": agency.id, "external_route_id": ev.route_external_id},
                                {"agency_id": agency.id, "external_route_id": ev.route_external_id})
                db.flush()
                route_id = r.id
            if ev.trip_external_id and route_id:
                t, _ = _resolve(db, Trip, {"route_id": route_id, "external_trip_id": ev.trip_external_id},
                                {"route_id": route_id, "external_trip_id": ev.trip_external_id})
                db.flush()
                trip_id = t.id
            if ev.vehicle_external_id:
                v, _ = _resolve(db, Vehicle, {"agency_id": agency.id, "external_vehicle_id": ev.vehicle_external_id},
                                {"agency_id": agency.id, "external_vehicle_id": ev.vehicle_external_id})
                db.flush()
                vehicle_id = v.id
            if ev.stop_external_id:
                s, _ = _resolve(db, Stop, {"agency_id": agency.id, "external_stop_id": ev.stop_external_id},
                                {"agency_id": agency.id, "external_stop_id": ev.stop_external_id})
                db.flush()
                stop_id = s.id
            db.add(TransitEvent(agency_id=agency.id, route_id=route_id, trip_id=trip_id,
                                vehicle_id=vehicle_id, stop_id=stop_id, event_type=ev.event_type,
                                observed_at=ev.observed_at, scheduled_at=ev.scheduled_at,
                                delay_seconds=ev.delay_seconds, latitude=ev.lat, longitude=ev.lon,
                                status="OBSERVED", source="gtfs-rt", source_event_id=ev.source_event_id,
                                raw_payload=ev.raw, normalized_payload={"delay_seconds": ev.delay_seconds}))
            db.commit()
            ingested += 1
        except Exception as exc:
            db.rollback()
            errors += 1
            log.warning(f"persist_error: {exc}")
    log.info(f"events_ingested ingested={ingested} duplicates={duplicates} errors={errors}")
    return {"ingested": ingested, "duplicates": duplicates, "errors": errors}
