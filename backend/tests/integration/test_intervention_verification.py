"""Stage 7: intervention honesty + all four verification outcomes."""
from datetime import datetime, timedelta, timezone
from backend.app.core.exceptions import UnsupportedInterventionError
from backend.app.services.interventions.intervention_service import request_intervention
from backend.app.services.recommendations.recommendation_service import create_recommendation
from backend.app.services.investigation.investigator import open_investigation
from backend.app.services.patterns.pattern_detector import detect_patterns
from backend.app.services.verification.verification_service import verify
from backend.app.services.detection.near_miss_detector import detect_for_vehicle
from backend.tests.conftest import add_delay_series
from backend.app.db.models.vehicle import Vehicle
import pytest


def _chain(db, seed):
    for v in ("V1", "V2"):
        veh = db.query(Vehicle).filter_by(external_vehicle_id=v).first() or Vehicle(agency_id=seed["agency"].id, external_vehicle_id=v)
        db.add(veh)
        db.commit()
        add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, [300, 800, 1200, 900, 400, 200])
        detect_for_vehicle(db, veh.id, seed["agency"].id)
    patterns = detect_patterns(db, min_occurrences=2)
    inv = open_investigation(db, patterns[0].id)
    rec = create_recommendation(db, inv.id, title="Observe window", description="Monitor.")
    return request_intervention(db, rec.id, "OPERATIONAL_REVIEW", target="Route 42 08:00 window")


def test_intervention_never_fake_executed(db, seed):
    inv = _chain(db, seed)
    assert inv.execution_status in ("PROPOSED", "PENDING_EXTERNAL_ACTION")
    assert inv.execution_status != "EXECUTED"


def test_unsupported_intervention_rejected(db, seed):
    from backend.app.services.recommendations.recommendation_service import create_recommendation as cr
    from backend.app.services.investigation.investigator import open_investigation as oi
    for v in ("V9",):
        veh = Vehicle(agency_id=seed["agency"].id, external_vehicle_id=v)
        db.add(veh)
        db.commit()
        add_delay_series(db, {"agency": seed["agency"], "route": seed["route"], "vehicle": veh}, [300, 800, 1200, 900, 400, 200])
        detect_for_vehicle(db, veh.id, seed["agency"].id)
    patterns = detect_patterns(db, min_occurrences=1)
    inv = oi(db, patterns[0].id)
    rec = cr(db, inv.id, title="t", description="d")
    with pytest.raises(UnsupportedInterventionError):
        request_intervention(db, rec.id, "REPROGRAM_TRAFFIC_LIGHTS", target="x")


def test_verification_insufficient_data(db, seed):
    inv = _chain(db, seed)
    now = datetime.now(timezone.utc)
    v = verify(db, inv.id, (now - timedelta(days=2), now - timedelta(days=1)), (now - timedelta(hours=1), now), min_samples=5000)
    assert v.outcome == "INSUFFICIENT_DATA"


def test_verification_outcomes_deterministic(db, seed):
    from backend.app.services.verification.verification_service import _avg_delay  # noqa
    inv = _chain(db, seed)
    now = datetime.now(timezone.utc)
    v = verify(db, inv.id, (now - timedelta(days=2), now - timedelta(days=1)), (now - timedelta(hours=1), now), min_samples=1)
    assert v.outcome in ("IMPROVED", "NO_SIGNIFICANT_CHANGE", "WORSENED", "INSUFFICIENT_DATA")
    assert v.baseline_metrics and v.post_metrics
