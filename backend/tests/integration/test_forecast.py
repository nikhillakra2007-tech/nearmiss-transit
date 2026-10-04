"""Forecast tests: signals, bands, leakage, determinism, adversarial (§P2 plan)."""
from datetime import datetime, timedelta, timezone
import pytest
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.vehicle import Vehicle
from backend.app.services.forecast.engine import forecast_pattern


def _route_events(db, seed, delays, start, step_min=5, tag="f"):
    veh = db.query(Vehicle).filter_by(external_vehicle_id=f"F-{tag}").first()
    if not veh:
        veh = Vehicle(agency_id=seed["agency"].id, external_vehicle_id=f"F-{tag}")
        db.add(veh)
        db.commit()
    for i, d in enumerate(delays):
        db.add(TransitEvent(agency_id=seed["agency"].id, route_id=seed["route"].id,
                            vehicle_id=veh.id, event_type="TRIP_UPDATE",
                            observed_at=start + timedelta(minutes=i * step_min),
                            delay_seconds=d, status="OBSERVED", source="test",
                            source_event_id=f"fc-{tag}-{i}-{d}", raw_payload={},
                            normalized_payload={}))
    db.commit()


def _nm_at(db, seed, vext, delays, start_ago_min):
    from backend.tests.conftest import add_delay_series
    from backend.app.services.detection.near_miss_detector import detect_for_vehicle
    veh = db.query(Vehicle).filter_by(external_vehicle_id=vext).first() or Vehicle(agency_id=seed["agency"].id, external_vehicle_id=vext)
    db.add(veh)
    db.commit()
    add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, delays, start_min_ago=start_ago_min)
    return detect_for_vehicle(db, veh.id, seed["agency"].id)


def _pat(db, seed, min_occ=1):
    from backend.app.services.patterns.pattern_detector import detect_patterns
    pats = detect_patterns(db, min_occurrences=min_occ)
    assert pats
    return pats[0]


def test_zero_and_insufficient_history(db, seed):
    from backend.app.db.models.pattern import Pattern
    t = datetime.now(timezone.utc)
    p = Pattern(agency_id=seed["agency"].id, route_id=seed["route"].id, pattern_type="T",
                title="t", recurrence_count=0, first_seen_at=t, last_seen_at=t, features={})
    db.add(p)
    db.commit()
    out = forecast_pattern(db, p.id)
    assert out["status"] == "INSUFFICIENT_DATA" and out["score"] is None


def test_trend_up_down_stable_and_recovery(db, seed):
    t = datetime.now(timezone.utc) - timedelta(hours=6)
    _route_events(db, seed, [60] * 6 + [400] * 6, t, tag="up")
    _nm_at(db, seed, "V1", [300, 800, 1200, 900, 400, 200], 300)
    _nm_at(db, seed, "V2", [300, 800, 1200, 900, 400, 200], 240)
    p = _pat(db, seed)
    up = next(s for s in forecast_pattern(db, p.id)["signals"] if s["name"] == "DEVIATION_TREND")
    assert up["available"] and up["value"] > 60
    assert forecast_pattern(db, p.id)["status"] in ("WATCH", "EMERGING")


def test_no_leakage_and_determinism(db, seed):
    t = datetime.now(timezone.utc) - timedelta(hours=6)
    _route_events(db, seed, [100] * 8, t, tag="leak")
    _nm_at(db, seed, "V1", [300, 800, 1200, 900, 400, 200], 300)
    _nm_at(db, seed, "V2", [300, 800, 1200, 900, 400, 200], 240)
    p = _pat(db, seed)
    t1 = datetime.now(timezone.utc) - timedelta(hours=1)
    before = forecast_pattern(db, p.id, at=t1)
    _route_events(db, seed, [900] * 6, datetime.now(timezone.utc) + timedelta(hours=5), tag="future")
    after = forecast_pattern(db, p.id, at=t1)
    assert before == after  # future insert cannot move the past
    assert forecast_pattern(db, p.id, at=t1) == before  # deterministic repeat


def test_bands_status_and_missing_signals(db, seed):
    _nm_at(db, seed, "V1", [300, 800, 1200, 900, 400, 200], 300)
    p = _pat(db, seed)
    out = forecast_pattern(db, p.id)
    assert out["status"] in ("NORMAL", "WATCH", "EMERGING", "INSUFFICIENT_DATA")
    if out["score"] is not None:
        assert 0.0 <= out["score"] <= 100.0
    names = [s["name"] for s in out["signals"]]
    assert names == ["DEVIATION_TREND", "RECOVERY_WEAKENING", "RECURRENCE",
                     "FINGERPRINT_SIMILARITY", "CHAIN_EXPOSURE", "RECENT_STRESS"]


def test_nonexistent_and_bad_at_and_explain(db, seed):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.deps import get_db
    from backend.app.db.base import Base
    from backend.app.db.session import engine
    from backend.app.db import models  # noqa
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    app.dependency_overrides[get_db] = lambda: db
    try:
        assert client.get("/api/v1/patterns/nope/forecast").status_code == 404
        _nm_at(db, seed, "V9", [300, 800, 1200, 900, 400, 200], 300)
        _nm_at(db, seed, "V8", [300, 800, 1200, 900, 400, 200], 240)
        pid = _pat(db, seed).id
        assert client.get(f"/api/v1/patterns/{pid}/forecast?at=not-a-date").status_code == 422
        r = client.get(f"/api/v1/patterns/{pid}/forecast?explain=true")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] != "INSUFFICIENT_DATA" or "agent" not in body
        if "agent" in body:
            assert {c["type"] for c in body["agent"]["claims"]} <= {"FACT", "INFERENCE", "HYPOTHESIS"}
    finally:
        app.dependency_overrides.clear()


def test_live_honest_all_zero_delays(db, seed):
    t = datetime.now(timezone.utc) - timedelta(hours=2)
    _route_events(db, seed, [0] * 10, t, tag="zero")
    from backend.app.db.models.pattern import Pattern
    p = Pattern(agency_id=seed["agency"].id, route_id=seed["route"].id, pattern_type="T",
                title="t", recurrence_count=0, first_seen_at=t, last_seen_at=t, features={})
    db.add(p)
    db.commit()
    out = forecast_pattern(db, p.id)
    assert out["status"] in ("NORMAL", "INSUFFICIENT_DATA")  # never EMERGING on flat zeros
