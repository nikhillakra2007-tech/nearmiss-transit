from backend.app.services.ingestion.gtfs_parser import parse_fixture_dicts
from backend.app.services.ingestion.normalizer import normalize
from backend.app.services.ingestion.ingestion_service import persist_normalized
from backend.app.services.detection.near_miss_detector import detect_for_vehicle
from backend.app.services.patterns.pattern_detector import detect_patterns
from backend.app.services.investigation.investigator import open_investigation
from backend.app.services.agent.orchestrator import investigate_with_agent
from backend.tests.conftest import add_delay_series


def test_ingestion_idempotent(db, seed):
    rows = parse_fixture_dicts([{"entity_id": "e1", "kind": "vehicle", "trip_id": "T1",
                                 "route_id": "42", "vehicle_id": "V1", "timestamp": 1700000000}])
    normed = [normalize(r, "test-agency") for r in rows]
    r1 = persist_normalized(db, normed)
    r2 = persist_normalized(db, normed)
    assert r1["ingested"] == 1 and r2["duplicates"] == 1 and r2["ingested"] == 0


def test_near_miss_pipeline(db, seed):
    add_delay_series(db, seed, [300, 540, 900, 1080, 960, 600, 360, 240])
    nm = detect_for_vehicle(db, seed["vehicle"].id, seed["agency"].id)
    assert nm is not None and nm.recovery_event_id is not None


def test_plain_delay_is_not_near_miss(db, seed):
    add_delay_series(db, seed, [60, 90, 120, 100, 80])
    assert detect_for_vehicle(db, seed["vehicle"].id, seed["agency"].id) is None


def test_end_to_end_pattern_investigation_agent(db, seed):
    from backend.app.db.models.vehicle import Vehicle
    from backend.app.db.models.agency import Agency
    for v in ("V1", "V2", "V3"):
        veh = db.query(Vehicle).filter_by(external_vehicle_id=v).first()
        if not veh:
            veh = Vehicle(agency_id=seed["agency"].id, external_vehicle_id=v)
            db.add(veh)
            db.commit()
        import backend.tests.conftest as C
        s2 = {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}
        C.add_delay_series(db, s2, [300, 700, 1100, 900, 500, 200])
        detect_for_vehicle(db, veh.id, seed["agency"].id)
    patterns = detect_patterns(db, min_occurrences=2)
    assert len(patterns) >= 1
    inv = open_investigation(db, patterns[0].id)
    result = investigate_with_agent(db, inv.id, patterns[0].id)
    assert "recommendation_id" in result
