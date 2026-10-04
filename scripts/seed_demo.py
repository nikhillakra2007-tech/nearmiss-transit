"""Seed DEMO/REPLAY data (clearly labelled, never presented as live).
Includes a deterministic Route 42 -> Route 17 lagged replay sequence
(4 windows) for the operational-domino story. Usage: python scripts/seed_demo.py"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta, timezone
from backend.app.db.session import SessionLocal
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.db import models  # noqa
from backend.app.db.models.agency import Agency
from backend.app.db.models.route import Route
from backend.app.db.models.vehicle import Vehicle
from backend.app.db.models.transit_event import TransitEvent


def _route(db, agency, ext):
    r = db.query(Route).filter_by(agency_id=agency.id, external_route_id=ext).first()
    if not r:
        r = Route(agency_id=agency.id, external_route_id=ext, short_name=ext)
        db.add(r)
        db.commit()
        db.refresh(r)
    return r


def _vehicle(db, agency, ext):
    v = db.query(Vehicle).filter_by(agency_id=agency.id, external_vehicle_id=ext).first()
    if not v:
        v = Vehicle(agency_id=agency.id, external_vehicle_id=ext)
        db.add(v)
        db.commit()
        db.refresh(v)
    return v


def _add_series(db, agency, route, veh, at, delays, tag):
    for i, d in enumerate(delays):
        sid = f"demo-{tag}-{i}"
        if db.query(TransitEvent).filter_by(agency_id=agency.id, source_event_id=sid).first():
            continue  # idempotent re-seed
        db.add(TransitEvent(agency_id=agency.id, route_id=route.id, vehicle_id=veh.id,
                            event_type="TRIP_UPDATE", observed_at=at + timedelta(minutes=i * 5),
                            delay_seconds=d, status="OBSERVED", source="DEMO/REPLAY",
                            source_event_id=sid, raw_payload={"demo": True},
                            normalized_payload={"delay_seconds": d}))
    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    agency = db.query(Agency).filter_by(external_id="demo-agency").first()
    if not agency:
        agency = Agency(external_id="demo-agency", name="Demo Agency (REPLAY)")
        db.add(agency)
        db.commit()
        db.refresh(agency)
    r42 = _route(db, agency, "42")
    r17 = _route(db, agency, "17")
    r8 = _route(db, agency, "8")
    base = datetime.now(timezone.utc) - timedelta(hours=2)
    for v in ("V1", "V2", "V3"):
        _add_series(db, agency, r42, _vehicle(db, agency, v), base, [300, 700, 1100, 900, 500, 200], v)
    # Domino replay: 4 windows, Route 17 spike lags Route 42 spike by ~12 min.
    for k in range(4):
        wb = base - timedelta(hours=3 * (k + 1))
        _add_series(db, agency, r42, _vehicle(db, agency, f"C42-{k}"), wb, [300, 700, 1100, 900, 500, 200], f"C42-{k}")
        _add_series(db, agency, r17, _vehicle(db, agency, f"C17-{k}"), wb + timedelta(minutes=12), [250, 650, 1000, 800, 450, 180], f"C17-{k}")
        _add_series(db, agency, r8, _vehicle(db, agency, f"C8-{k}"), wb + timedelta(minutes=24), [100, 300, 900, 700, 400, 150], f"C8-{k}")
    # Emerging tail (REPLAY): recent sub-threshold rising delays on route 42.
    # Peak stays below the near-miss threshold: EMERGING before a new near-miss.
    tail_at = datetime.now(timezone.utc) - timedelta(minutes=45)
    tail_veh = _vehicle(db, agency, "TAIL-1")
    _add_series(db, agency, r42, tail_veh, tail_at,
                [400, 430, 460, 480, 500, 520, 540, 560, 580], "TAIL-1")
    # Normal background ops (REPLAY): low everyday delays so baselines stay honest.
    bg_veh = _vehicle(db, agency, "BG-1")
    for j, d in enumerate([60, 90, 120, 80, 110, 70, 100, 130, 90, 105, 75, 140,
                           65, 95, 125, 85, 115, 140, 70, 100, 120, 80, 110, 90]):
        _add_series(db, agency, r42, bg_veh,
                    datetime.now(timezone.utc) - timedelta(hours=72 - j * 2.5),
                    [d], f"BG-1-{j}")
    print("demo seed complete (DEMO/REPLAY mode, incl. 42->17 chain windows)")
