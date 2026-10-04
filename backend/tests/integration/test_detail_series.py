"""delay_series micro-fix regression: persisted-only, windowed, ordered, safe, compatible."""
from fastapi.testclient import TestClient
from backend.app.api.routes.detail import delay_series_for
from backend.app.db.base import Base
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.vehicle import Vehicle
from backend.app.db.session import engine
from backend.app.db import models  # noqa
from backend.app.main import app
from backend.app.services.detection.near_miss_detector import detect_for_vehicle
from backend.app.services.patterns.pattern_detector import detect_patterns
from backend.tests.conftest import add_delay_series

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def _chain(db, seed):
    for v in ("V1", "V2"):
        veh = db.query(Vehicle).filter_by(external_vehicle_id=v).first() or Vehicle(agency_id=seed["agency"].id, external_vehicle_id=v)
        db.add(veh)
        db.commit()
        add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, [300, 800, 1200, 900, 400, 200])
        detect_for_vehicle(db, veh.id, seed["agency"].id)
    return detect_patterns(db, min_occurrences=2)


def test_series_present_from_persisted_events(db, seed):
    pats = _chain(db, seed)
    nm_id = pats[0].id
    from backend.app.db.models.near_miss import NearMiss
    from backend.app.db.models.pattern import NearMissPattern
    link = db.query(NearMissPattern).filter_by(pattern_id=nm_id).first()
    nm = db.query(NearMiss).get(link.near_miss_id)
    start = db.query(TransitEvent).get(nm.start_event_id)
    rec = db.query(TransitEvent).get(nm.recovery_event_id)
    series = delay_series_for(db, nm, start, rec)
    assert isinstance(series, list) and len(series) >= 4  # present
    persisted = {(e.observed_at.isoformat(), round(e.delay_seconds / 60.0, 1))
                 for e in db.query(TransitEvent).filter_by(vehicle_id=nm.vehicle_id)
                 if e.delay_seconds is not None}
    for pt in series:  # every point matches a persisted row
        assert (pt["timestamp"], pt["delay_minutes"]) in persisted
        assert set(pt.keys()) == {"timestamp", "delay_minutes"}
    ts = [p["timestamp"] for p in series]  # chronological + windowed
    assert ts == sorted(ts) and all(start.observed_at.isoformat() <= t <= rec.observed_at.isoformat() for t in ts)


def test_empty_series_handled_safely(db, seed):
    from backend.app.db.models.near_miss import NearMiss
    pats = _chain(db, seed)
    assert delay_series_for(db, db.query(NearMiss).first(), None, None) == []


def test_detail_backward_compatible(db, seed):
    from backend.app.api.deps import get_db
    pats = _chain(db, seed)
    app.dependency_overrides[get_db] = lambda: db
    try:
        r = client.get(f"/api/v1/patterns/{pats[0].id}/detail")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"pattern", "members", "investigations"}  # shape unchanged
    m = body["members"][0]
    for key in ("start_event", "recovery_event", "abnormal_value", "detection_reason"):
        assert key in m  # existing fields intact
    assert isinstance(m["delay_series"], list)  # only addition
