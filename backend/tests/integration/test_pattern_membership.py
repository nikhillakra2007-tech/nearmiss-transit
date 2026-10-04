"""V2 regression: late-arriving near-misses join existing patterns (link sync)."""
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.services.patterns.pattern_detector import detect_patterns
from backend.tests.conftest import add_delay_series
from backend.app.db.models.vehicle import Vehicle
from backend.app.services.detection.near_miss_detector import detect_for_vehicle


def test_late_members_linked_on_redetection(db, seed):
    veh = db.query(Vehicle).filter_by(external_vehicle_id="V1").first()
    add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, [300, 800, 1200, 900, 400, 200])
    detect_for_vehicle(db, veh.id, seed["agency"].id)
    first = detect_patterns(db, min_occurrences=1)
    n0 = db.query(NearMissPattern).filter_by(pattern_id=first[0].id).count()
    v2 = Vehicle(agency_id=seed["agency"].id, external_vehicle_id="V99")
    db.add(v2)
    db.commit()
    add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": v2}, [300, 800, 1200, 900, 400, 200])
    detect_for_vehicle(db, v2.id, seed["agency"].id)
    detect_patterns(db, min_occurrences=1)
    n1 = db.query(NearMissPattern).filter_by(pattern_id=first[0].id).count()
    assert n1 == n0 + 1
