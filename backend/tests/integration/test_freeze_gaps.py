"""Pre-frontend freeze gap tests: cancellation/failure exclusion, sustained delay,
short series, pattern idempotency, directional verification outcomes."""
from datetime import datetime, timedelta, timezone
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.vehicle import Vehicle
from backend.app.services.detection.near_miss_detector import detect_for_vehicle
from backend.app.services.patterns.pattern_detector import detect_patterns
from backend.app.services.verification.verification_service import verify
from backend.tests.conftest import add_delay_series


def test_cancellation_is_failure_not_nearmiss(db, seed):
    add_delay_series(db, seed, [300, 700, 1100, 900, 500, 200])
    db.add(TransitEvent(agency_id=seed["agency"].id, route_id=seed["route"].id,
                        vehicle_id=seed["vehicle"].id, event_type="CANCELLATION",
                        observed_at=datetime.now(timezone.utc), status="CANCELLED",
                        source="test", source_event_id="cancel-1",
                        raw_payload={}, normalized_payload={}))
    db.commit()
    assert detect_for_vehicle(db, seed["vehicle"].id, seed["agency"].id) is None


def test_sustained_delay_without_recovery_is_not_nearmiss(db, seed):
    add_delay_series(db, seed, [700, 900, 1100, 1200, 1300, 1400])
    assert detect_for_vehicle(db, seed["vehicle"].id, seed["agency"].id) is None


def test_short_series_insufficient_data(db, seed):
    add_delay_series(db, seed, [1200, 200])
    assert detect_for_vehicle(db, seed["vehicle"].id, seed["agency"].id) is None


def test_pattern_detection_idempotent(db, seed):
    for v in ("V1", "V2"):
        veh = db.query(Vehicle).filter_by(external_vehicle_id=v).first() or Vehicle(agency_id=seed["agency"].id, external_vehicle_id=v)
        db.add(veh)
        db.commit()
        add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, [300, 800, 1200, 900, 400, 200])
        detect_for_vehicle(db, veh.id, seed["agency"].id)
    first = detect_patterns(db, min_occurrences=2)
    second = detect_patterns(db, min_occurrences=2)
    assert len(first) == len(second) == 1 and first[0].id == second[0].id


def _seed_window(db, seed, vehicle, delays, center):
    for i, d in enumerate(delays):
        db.add(TransitEvent(agency_id=seed["agency"].id, route_id=seed["route"].id,
                            vehicle_id=vehicle.id, event_type="TRIP_UPDATE",
                            observed_at=center + timedelta(minutes=i), delay_seconds=d,
                            status="OBSERVED", source="test",
                            source_event_id=f"win-{vehicle.external_vehicle_id}-{center.isoformat()}-{i}",
                            raw_payload={}, normalized_payload={}))
    db.commit()


def test_verification_improved_and_worsened_reachable(db, seed):
    from backend.app.services.recommendations.recommendation_service import create_recommendation
    from backend.app.services.investigation.investigator import open_investigation
    from backend.app.services.interventions.intervention_service import request_intervention
    for v in ("V1", "V2"):
        veh = db.query(Vehicle).filter_by(external_vehicle_id=v).first() or Vehicle(agency_id=seed["agency"].id, external_vehicle_id=v)
        db.add(veh)
        db.commit()
        add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, [300, 800, 1200, 900, 400, 200])
        detect_for_vehicle(db, veh.id, seed["agency"].id)
    pats = detect_patterns(db, min_occurrences=2)
    inv = open_investigation(db, pats[0].id)
    rec = create_recommendation(db, inv.id, title="t", description="d")
    itv = request_intervention(db, rec.id, "OPERATIONAL_REVIEW", target="window")
    now = datetime.now(timezone.utc)
    veh = db.query(Vehicle).first()
    _seed_window(db, seed, veh, [1200, 1300, 1100, 1250, 1150], now - timedelta(days=2))
    _seed_window(db, seed, veh, [100, 120, 90, 110, 100], now - timedelta(hours=12))
    v = verify(db, itv.id, (now - timedelta(days=3), now - timedelta(days=1)), (now - timedelta(days=1), now), min_samples=1)
    assert v.outcome == "IMPROVED", v.explanation
    v2 = verify(db, itv.id, (now - timedelta(days=1), now), (now - timedelta(days=3), now - timedelta(days=1)), min_samples=1)
    assert v2.outcome == "WORSENED", v2.explanation
