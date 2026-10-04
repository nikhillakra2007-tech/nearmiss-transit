"""V2.6 early-warning replay tests: contract, transitions, no-leakage,
determinism, typed errors, safety language, frontend presence."""
import json
import re
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.app.api.deps import get_db
from backend.app.db.models.pattern import Pattern
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.vehicle import Vehicle
from backend.app.main import app
from backend.app.services.forecast.engine import forecast_pattern
from backend.app.services.forecast.replay import replay_early_warning

SHAPE = [300, 800, 1200, 900, 400, 200]
BANNED = ["will fail", "guarantee", "unsafe", "dangerous", "accident",
          "prediction certainty", "predicted failure", "caused by"]
BANNED_WORDS = [r"\bcause\b", r"\bcauses\b", r"\bcaused\b", r"\bguaranteed\b"]


def _nm(db, seed, vext, delays, ago):
    from backend.tests.conftest import add_delay_series
    from backend.app.services.detection.near_miss_detector import detect_for_vehicle
    veh = Vehicle(agency_id=seed["agency"].id, external_vehicle_id=vext)
    db.add(veh)
    db.commit()
    add_delay_series(db, {"agency": seed["agency"], "route": seed["route"],
                          "vehicle": veh}, delays, start_min_ago=ago)
    return detect_for_vehicle(db, veh.id, seed["agency"].id)


def _pat(db, min_occ=2):
    from backend.app.services.patterns.pattern_detector import detect_patterns
    pats = detect_patterns(db, min_occurrences=min_occ)
    assert pats
    return pats[0]


def _calm(db, seed):
    assert _nm(db, seed, "C1", SHAPE, 300)
    assert _nm(db, seed, "C2", SHAPE, 240)
    return _pat(db)


def _heavy(db, seed):
    from backend.app.db.models.route import Route
    for k, ago in enumerate([600, 500, 400, 300, 200, 120]):
        assert _nm(db, seed, f"H{k}", SHAPE, ago)
    # second route pattern: enables the fingerprint-similarity signal
    rt17 = Route(agency_id=seed["agency"].id, external_route_id="17", short_name="17")
    db.add(rt17)
    db.commit()
    from backend.tests.conftest import add_delay_series
    from backend.app.services.detection.near_miss_detector import detect_for_vehicle
    from backend.app.db.models.vehicle import Vehicle as _V
    for k, ago in enumerate([500, 400]):
        veh = _V(agency_id=seed["agency"].id, external_vehicle_id=f"HO{k}")
        db.add(veh)
        db.commit()
        add_delay_series(db, {"agency": seed["agency"], "route": rt17, "vehicle": veh},
                         SHAPE, start_min_ago=ago)
        assert detect_for_vehicle(db, veh.id, seed["agency"].id)
    # rising route-level delay background on route 42
    bg = _V(agency_id=seed["agency"].id, external_vehicle_id="HBG")
    db.add(bg)
    db.commit()
    t0 = datetime.now(timezone.utc) - timedelta(minutes=700)
    for i, d in enumerate([60] * 10 + [300] * 10 + [500] * 10):
        db.add(TransitEvent(agency_id=seed["agency"].id, route_id=seed["route"].id,
                            vehicle_id=bg.id, event_type="TRIP_UPDATE",
                            observed_at=t0 + timedelta(minutes=i * 10),
                            delay_seconds=d, status="OBSERVED", source="test",
                            source_event_id=f"hbg-{i}", raw_payload={},
                            normalized_payload={}))
    db.commit()
    from backend.app.services.patterns.pattern_detector import detect_patterns
    pats = detect_patterns(db, min_occurrences=2)
    mine = [p for p in pats if p.route_id == seed["route"].id]
    assert mine
    return mine[0]


def _rising(db, seed):
    for k, ago in enumerate([400, 340, 280, 220, 160, 100]):
        assert _nm(db, seed, f"A{k}", SHAPE, ago)
    return _pat(db)


def _client(db):
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _teardown():
    app.dependency_overrides.clear()


def _blob(payload: dict) -> str:
    return json.dumps(payload, default=str).lower()


def test_endpoint_happy_path(db, seed):
    pid = _heavy(db, seed).id
    client = _client(db)
    try:
        r = client.get(f"/api/v1/patterns/{pid}/early-warning")
        assert r.status_code == 200
        body = r.json()
        assert body["timeline"] and body["target_near_miss_id"]
        assert body["target_timestamp"] and body["available_history"]["cutoffs_evaluated"] >= 2
        assert body["status"] == "COMPLETE"
    finally:
        _teardown()


def test_historical_replay_mode_returned(db, seed):
    pid = _calm(db, seed).id
    out = replay_early_warning(db, pid)
    assert out["mode"] == "HISTORICAL_REPLAY"
    client = _client(db)
    try:
        assert client.get(f"/api/v1/patterns/{pid}/early-warning").json()["mode"] == "HISTORICAL_REPLAY"
    finally:
        _teardown()


def test_first_watch_detection(db, seed):
    pid = _rising(db, seed).id
    out = replay_early_warning(db, pid, lookback_minutes=180, step_minutes=30)
    fw = out["first_watch"]
    assert fw and fw["band"] == "WATCH" and fw["score"] >= 30
    assert fw["minutes_before_target"] > 0
    assert out["first_emerging"] is None  # rising shape never reaches EMERGING


def test_first_emerging_detection(db, seed):
    pid = _heavy(db, seed).id
    out = replay_early_warning(db, pid, lookback_minutes=120, step_minutes=15)
    fe = out["first_emerging"]
    assert fe and fe["band"] == "EMERGING" and fe["score"] > 60
    assert fe["minutes_before_target"] >= 0
    assert out["first_watch"] is not None


def test_no_threshold_crossing_returns_null(db, seed):
    pid = _calm(db, seed).id
    out = replay_early_warning(db, pid)
    assert out["status"] == "COMPLETE"  # scored NORMAL timeline, not missing data
    assert out["first_watch"] is None and out["first_emerging"] is None
    assert all(p["band"] == "NORMAL" or p["score"] is None for p in out["timeline"])


def test_insufficient_history(db, seed):
    t = datetime.now(timezone.utc)
    p = Pattern(agency_id=seed["agency"].id, route_id=seed["route"].id,
                pattern_type="T", title="empty", recurrence_count=0,
                first_seen_at=t, last_seen_at=t, features={})
    db.add(p)
    db.commit()
    client = _client(db)
    try:
        r = client.get(f"/api/v1/patterns/{p.id}/early-warning")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "INSUFFICIENT_DATA" and body["timeline"] == []
        assert body["first_watch"] is None and body["first_emerging"] is None
        assert body["mode"] == "HISTORICAL_REPLAY"
        assert all(v is None or v != 0 for v in
                   [body["first_watch"], body["first_emerging"]])
    finally:
        _teardown()


def test_invalid_lookback(db, seed):
    pid = _calm(db, seed).id
    client = _client(db)
    try:
        assert client.get(f"/api/v1/patterns/{pid}/early-warning?lookback_minutes=0").status_code == 422
        assert client.get(f"/api/v1/patterns/{pid}/early-warning?lookback_minutes=-5").status_code == 422
    finally:
        _teardown()


def test_invalid_step(db, seed):
    pid = _calm(db, seed).id
    client = _client(db)
    try:
        assert client.get(f"/api/v1/patterns/{pid}/early-warning?step_minutes=1").status_code == 422
        assert client.get(f"/api/v1/patterns/{pid}/early-warning?step_minutes=4").status_code == 422
    finally:
        _teardown()


def test_maximum_lookback_cap(db, seed):
    pid = _calm(db, seed).id
    client = _client(db)
    try:
        assert client.get(f"/api/v1/patterns/{pid}/early-warning?lookback_minutes=181").status_code == 422
        assert client.get(f"/api/v1/patterns/{pid}/early-warning?lookback_minutes=500").status_code == 422
        assert client.get(f"/api/v1/patterns/{pid}/early-warning?lookback_minutes=180").status_code == 200
    finally:
        _teardown()


def test_no_future_data_leakage(db, seed):
    pid = _heavy(db, seed).id
    before = replay_early_warning(db, pid, lookback_minutes=120, step_minutes=30)
    cutoff = before["timeline"][2]["cutoff"]
    fc_before = forecast_pattern(db, pid, at=datetime.fromisoformat(cutoff))
    # large future event AFTER the target near-miss
    veh = Vehicle(agency_id=seed["agency"].id, external_vehicle_id="FUT")
    db.add(veh)
    db.commit()
    future = datetime.now(timezone.utc) + timedelta(hours=5)
    for i in range(8):
        db.add(TransitEvent(agency_id=seed["agency"].id, route_id=seed["route"].id,
                            vehicle_id=veh.id, event_type="TRIP_UPDATE",
                            observed_at=future + timedelta(minutes=i * 5),
                            delay_seconds=3600, status="OBSERVED", source="test",
                            source_event_id=f"leak-{i}", raw_payload={},
                            normalized_payload={}))
    db.commit()
    after = replay_early_warning(db, pid, lookback_minutes=120, step_minutes=30)
    assert after == before  # future observations cannot move earlier replay points
    assert forecast_pattern(db, pid, at=datetime.fromisoformat(cutoff)) == fc_before


def test_deterministic_repeated_replay(db, seed):
    pid = _rising(db, seed).id
    first = replay_early_warning(db, pid, lookback_minutes=180, step_minutes=30)
    second = replay_early_warning(db, pid, lookback_minutes=180, step_minutes=30)
    assert first == second


def test_existing_forecast_result_unchanged(db, seed):
    pid = _heavy(db, seed).id

    def _stable():
        out = forecast_pattern(db, pid)
        out.pop("evaluated_at", None)  # wall-clock stamp, not scoring state
        return out

    before = _stable()
    replay_early_warning(db, pid)
    replay_early_warning(db, pid, lookback_minutes=180, step_minutes=30)
    assert _stable() == before  # replay is read-only reuse


def test_typed_errors(db, seed):
    client = _client(db)
    try:
        r = client.get("/api/v1/patterns/does-not-exist/early-warning")
        assert r.status_code == 404 and "detail" in r.json()
        pid = _calm(db, seed).id
        r = client.get(f"/api/v1/patterns/{pid}/early-warning?at=not-a-date")
        assert r.status_code == 422 and "detail" in r.json()
        r = client.get(f"/api/v1/patterns/{pid}/early-warning?lookback_minutes=many")
        assert r.status_code == 422
    finally:
        _teardown()


def test_safety_language_sweep(db, seed):
    pid = _heavy(db, seed).id
    blob = _blob(replay_early_warning(db, pid, lookback_minutes=120, step_minutes=30))
    for phrase in BANNED:
        assert phrase not in blob, f"banned phrase in payload: {phrase}"
    for pattern in BANNED_WORDS:
        assert not re.search(pattern, blob), f"banned word in payload: {pattern}"
    import pathlib
    # Scope: the feature's new output (payload) and new service file.
    # (Pre-existing repo copy such as "not a guaranteed prediction" in the
    # older forecast card is out of scope and intentionally untouched.)
    text = pathlib.Path("backend/app/services/forecast/replay.py").read_text(encoding="utf-8").lower()
    for phrase in BANNED:
        assert phrase not in text, f"banned phrase in replay.py: {phrase}"
    for pattern in BANNED_WORDS:
        assert not re.search(pattern, text), f"banned word in replay.py: {pattern}"


def test_frontend_served_correctly():
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert client.get("/app.js").status_code == 200
    assert client.get("/styles.css").status_code == 200


def test_replay_badge_present():
    client = TestClient(app)
    js = client.get("/app.js").text
    assert "HISTORICAL REPLAY" in js
    assert "early-warning" in js


def test_accessible_text_representation_present():
    client = TestClient(app)
    js = client.get("/app.js").text
    assert "<table>" in js and "text alternative" in js
    assert "<select" in js and "aria-label" in js
