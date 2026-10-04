"""Pytest fixtures: file SQLite DB, seeded agency/route/vehicle + demo event series."""
from __future__ import annotations
import os
import tempfile
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base
from backend.app.db import models  # noqa
from backend.app.db.models.agency import Agency
from backend.app.db.models.route import Route
from backend.app.db.models.vehicle import Vehicle
from backend.app.db.models.transit_event import TransitEvent


@pytest.fixture()
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    yield session
    session.close()
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture()
def seed(db):
    agency = Agency(external_id="test-agency", name="Test Agency")
    db.add(agency)
    db.commit()
    db.refresh(agency)
    route = Route(agency_id=agency.id, external_route_id="42", short_name="42")
    db.add(route)
    db.commit()
    db.refresh(route)
    vehicle = Vehicle(agency_id=agency.id, external_vehicle_id="V1", label="V1")
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return {"agency": agency, "route": route, "vehicle": vehicle}


def add_delay_series(db, seed, delays: list[int], start_min_ago: int = 60) -> list:
    import uuid as _uuid
    base = datetime.now(timezone.utc) - timedelta(minutes=start_min_ago)
    tag = (seed["vehicle"].id[:8] if seed.get("vehicle") else _uuid.uuid4().hex[:8])
    events = []
    for i, d in enumerate(delays):
        e = TransitEvent(agency_id=seed["agency"].id, route_id=seed["route"].id,
                         vehicle_id=seed["vehicle"].id, event_type="TRIP_UPDATE",
                         observed_at=base + timedelta(minutes=i * 2), delay_seconds=d,
                         status="OBSERVED", source="test", source_event_id=f"evt-{tag}-{d}-{i}",
                         raw_payload={}, normalized_payload={})
        db.add(e)
        events.append(e)
    db.commit()
    return events
