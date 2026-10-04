"""Fingerprint + resilience + V2.2 API + safety tests."""
from backend.app.services.agent.safety import validate_safe_output
from backend.app.core.exceptions import AgentOutputRejectedError
from backend.app.services.fingerprints.engine import (
    classify, fingerprint_for, peak_bucket, recovery_bucket, similar_patterns,
    similarity, time_bucket)
import pytest


def test_buckets_and_determinism(db, seed):
    assert time_bucket(18) == "EVENING" and peak_bucket(16) == "HIGH"
    assert recovery_bucket(300) == "MODERATE" and recovery_bucket(None) == "UNKNOWN"
    assert classify(87) == "HIGH_MATCH" and classify(60) == "PARTIAL_MATCH" and classify(10) == "LOW_SIMILARITY"
    a = {"route": "42", "type": "T", "time_bucket": "EVENING", "peak_bucket": "HIGH",
         "recovery_bucket": "MODERATE", "recurrence_strength": "STRONG_RECURRING", "chain_exposure": True}
    assert similarity(a, dict(a)) == (100.0, ["route", "type", "time", "peak", "recovery", "recurrence", "chain"])
    b = dict(a, route="17", peak_bucket="LOW")
    s, matched = similarity(a, b)
    assert s == 65.0 and "route" not in matched and "peak" not in matched


def _chain2(db, seed):
    from backend.app.db.models.vehicle import Vehicle
    from backend.app.services.detection.near_miss_detector import detect_for_vehicle
    from backend.app.services.patterns.pattern_detector import detect_patterns
    from backend.tests.conftest import add_delay_series
    for v in ("V1", "V2"):
        veh = db.query(Vehicle).filter_by(external_vehicle_id=v).first() or Vehicle(agency_id=seed["agency"].id, external_vehicle_id=v)
        db.add(veh)
        db.commit()
        add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, [300, 800, 1200, 900, 400, 200])
        detect_for_vehicle(db, veh.id, seed["agency"].id)
    return detect_patterns(db, min_occurrences=2)


def test_fingerprint_and_similar_api(db, seed):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.deps import get_db
    pats = _chain2(db, seed)
    fp = fingerprint_for(db, pats[0].id)
    assert set(fp) >= {"canonical_id", "route", "time_bucket", "peak_bucket", "recurrence_strength"}
    assert fp["canonical_id"].count("|") == 6
    assert fingerprint_for(db, pats[0].id) == fp  # deterministic
    client = TestClient(app)
    app.dependency_overrides[get_db] = lambda: db
    try:
        assert client.get(f"/api/v1/patterns/{pats[0].id}/fingerprint").status_code == 200
        assert client.get("/api/v1/patterns/nope/fingerprint").status_code == 404
        sim = client.get(f"/api/v1/patterns/{pats[0].id}/similar?n=5").json()["similar"]
        assert all(s["pattern_id"] != pats[0].id for s in sim)  # self excluded
    finally:
        app.dependency_overrides.clear()


def test_resilience_bounds_and_zero_data(db, seed):
    from backend.app.services.resilience.radar import overview, route_resilience
    assert route_resilience(db, seed["agency"].id, seed["route"].id)["status"] == "INSUFFICIENT_DATA"
    _chain2(db, seed)
    got = route_resilience(db, seed["agency"].id, seed["route"].id)
    assert got["status"] in ("OBSERVED_STRESS", "ELEVATED", "STABLE")
    assert 0.0 <= got["resilience"] <= 100.0
    assert set(got["signals"]) == {"frequency", "recurrence", "peak", "recovery", "chain", "trend"}
    items = overview(db, seed["agency"].id)
    assert items and items[0]["resilience"] is not None
    from backend.app.services.resilience.radar import route_resilience as rr2
    assert rr2(db, seed["agency"].id, "00000000-0000-0000-0000-000000000000")["status"] == "INSUFFICIENT_DATA"


def test_simulate_api_and_explain(db, seed):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.deps import get_db
    from backend.app.db.models.near_miss import NearMiss
    _chain2(db, seed)
    nm = db.query(NearMiss).first()
    client = TestClient(app)
    app.dependency_overrides[get_db] = lambda: db
    try:
        r = client.post(f"/api/v1/near-misses/{nm.id}/simulate", json={"scenario": "REDUCE_PEAK_PERCENT", "value": 25})
        assert r.status_code == 200 and r.json()["mode"] == "COUNTERFACTUAL"
        assert client.post(f"/api/v1/near-misses/{nm.id}/simulate", json={"scenario": "REDUCE_PEAK_PERCENT", "value": 0}).status_code == 422
        assert client.post(f"/api/v1/near-misses/{nm.id}/simulate", json={"scenario": "NOPE", "value": 10}).status_code == 422
        assert client.post("/api/v1/near-misses/nope/simulate", json={"scenario": "REDUCE_PEAK_PERCENT", "value": 10}).status_code == 404
        ex = client.post(f"/api/v1/near-misses/{nm.id}/simulate", json={"scenario": "REDUCE_PEAK_PERCENT", "value": 25, "explain": True}).json()
        assert "agent" in ex  # evidence may be absent; keys present regardless
    finally:
        app.dependency_overrides.clear()


def test_safety_bans():
    def out(stmt, typ="FACT"):
        return {"summary": "s", "claims": [{"type": typ, "statement": stmt, "evidence_ids": ["e1"], "confidence": 0.8}],
                "possible_causes": [], "recommendation": {"title": "t", "description": "d"}}
    for bad in ("This will prevent failures", "guaranteed improvement", "high accident risk",
                "low safety score", "failure probability 80%", "100% certain outcome",
                "Route 42 will fail tonight", "the line is unsafe", "dangerous conditions",
                "we guarantee improvement", "delays cause cancellations"):
        with pytest.raises(AgentOutputRejectedError):
            validate_safe_output(out(bad), {"e1"})
    sim = {"summary": "s", "claims": [{"type": "SIMULATION", "statement": "Simulated peak is lower.", "evidence_ids": ["e1"], "confidence": 0.9}],
           "possible_causes": [], "recommendation": {"title": "t", "description": "d"}}
    assert validate_safe_output(sim, {"e1"})
    with pytest.raises(AgentOutputRejectedError):
        validate_safe_output(out("x", typ="PROPHECY"), {"e1"})
