"""Sandbox tests: ranking, ties, validation, recommend+handoff, explain."""
from backend.app.services.sandbox.compare import compare, explain_ranking, recommend_best
from backend.app.services.counterfactual.lab import InvalidSimulationError
import pytest


def _nm(db, seed):
    from backend.app.db.models.vehicle import Vehicle
    from backend.tests.conftest import add_delay_series
    from backend.app.services.detection.near_miss_detector import detect_for_vehicle
    veh = db.query(Vehicle).filter_by(external_vehicle_id="V1").first()
    add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh},
                     [300, 800, 1200, 900, 400, 200])
    nm = detect_for_vehicle(db, veh.id, seed["agency"].id)
    assert nm
    return nm


def test_compare_ranking_and_ties(db, seed):
    nm = _nm(db, seed)
    out = compare(db, nm.id, [{"scenario": "REDUCE_PEAK_PERCENT", "value": 20},
                              {"scenario": "START_RECOVERY_EARLIER", "value": 1},
                              {"scenario": "REDUCE_RECOVERY_DURATION_PERCENT", "value": 25}])
    assert out["best"] and sorted(out["ranking"]) == [0, 1, 2]
    ranked_imps = [out["options"][i]["improvement"] for i in out["ranking"]]
    assert ranked_imps == sorted(ranked_imps, reverse=True)  # deterministic descending rank
    assert all(o["improvement"] is not None for o in out["options"])
    assert "guarantee" in out["note"].lower()
    again = compare(db, nm.id, [{"scenario": "REDUCE_PEAK_PERCENT", "value": 20},
                                {"scenario": "START_RECOVERY_EARLIER", "value": 1},
                                {"scenario": "REDUCE_RECOVERY_DURATION_PERCENT", "value": 25}])
    assert again == out  # deterministic


def test_invalid_and_insufficient(db, seed):
    nm = _nm(db, seed)
    with pytest.raises(InvalidSimulationError):
        compare(db, nm.id, [])
    with pytest.raises(InvalidSimulationError):
        compare(db, nm.id, [{"scenario": "NOPE", "value": 1}])
    with pytest.raises(InvalidSimulationError):
        compare(db, nm.id, [{"scenario": "REDUCE_PEAK_PERCENT", "value": float("nan")}])
    with pytest.raises(InvalidSimulationError):
        compare(db, nm.id, [{"scenario": "REDUCE_PEAK_PERCENT"}])
    with pytest.raises(InvalidSimulationError):
        compare(db, nm.id, [{"scenario": "REDUCE_PEAK_PERCENT", "value": 10}] * 6)


def test_recommend_handoff_and_explain(db, seed):
    from backend.app.services.patterns.pattern_detector import detect_patterns
    from backend.app.services.investigation.investigator import open_investigation
    nm = _nm(db, seed)
    _nm2 = None
    from backend.app.db.models.vehicle import Vehicle
    from backend.tests.conftest import add_delay_series as _ads
    from backend.app.services.detection.near_miss_detector import detect_for_vehicle as _det
    veh2 = Vehicle(agency_id=seed["agency"].id, external_vehicle_id="V2")
    db.add(veh2)
    db.commit()
    _ads(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh2}, [300, 800, 1200, 900, 400, 200])
    _det(db, veh2.id, seed["agency"].id)
    pats = detect_patterns(db, min_occurrences=2)
    inv = open_investigation(db, pats[0].id)
    assert inv
    res = recommend_best(db, nm.id, "START_RECOVERY_EARLIER", 1)
    assert res["improvement"] is not None and "PENDING_EXTERNAL_ACTION" in res["execution"]
    from backend.app.db.models.recommendation import Recommendation
    rec = db.query(Recommendation).get(res["recommendation_id"])
    assert rec.recommendation_type == "MODELED_INTERVENTION"
    out = compare(db, nm.id, [{"scenario": "START_RECOVERY_EARLIER", "value": 1}])
    agent = explain_ranking(db, {"near_miss_id": nm.id, **out})
    assert {c["type"] for c in agent["claims"]} <= {"FACT", "INFERENCE", "HYPOTHESIS", "SIMULATION"}


def test_sandbox_api(db, seed):
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from backend.app.api.deps import get_db
    nm = _nm(db, seed)
    client = TestClient(app)
    app.dependency_overrides[get_db] = lambda: db
    try:
        r = client.post(f"/api/v1/near-misses/{nm.id}/sandbox", json={})
        assert r.status_code == 200 and r.json()["best"]
        assert client.post("/api/v1/near-misses/nope/sandbox", json={}).status_code == 404
        assert client.post(f"/api/v1/near-misses/{nm.id}/sandbox", json={"scenarios": []}).status_code == 422
    finally:
        app.dependency_overrides.clear()
