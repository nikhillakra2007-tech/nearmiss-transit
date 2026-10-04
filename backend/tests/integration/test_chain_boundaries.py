"""V2.1 chain detector boundary conditions — deterministic, exact."""
from datetime import datetime, timedelta, timezone
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.route import Route
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.vehicle import Vehicle
from backend.app.services.chains.chain_detector import candidate_pairs, detect_chains


def _mk(db, seed, vext, dext, at, route=None):
    route = route or seed["route"]
    veh = db.query(Vehicle).filter_by(external_vehicle_id=vext).first()
    if not veh:
        veh = Vehicle(agency_id=seed["agency"].id, external_vehicle_id=vext)
        db.add(veh)
        db.commit()
    e = TransitEvent(agency_id=seed["agency"].id, route_id=route.id, vehicle_id=veh.id,
                     event_type="TRIP_UPDATE", observed_at=at, delay_seconds=900,
                     status="OBSERVED", source="test", source_event_id=f"b-{vext}-{dext}",
                     raw_payload={}, normalized_payload={})
    db.add(e)
    db.commit()
    nm = NearMiss(agency_id=seed["agency"].id, route_id=route.id, vehicle_id=veh.id,
                  start_event_id=e.id, detected_at=at, near_miss_type="T",
                  severity="HIGH", baseline_value={}, abnormal_value={"peak_delay": 900},
                  confidence_score=0.8, status="DETECTED", detection_reason="t")
    db.add(nm)
    db.commit()
    return nm


def test_exact_window_limit_included(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t)
    _mk(db, seed, "V2", "b", t + timedelta(minutes=120))
    assert len(candidate_pairs(db, seed["agency"].id, window_minutes=120)) == 1


def test_one_second_outside_excluded(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t)
    _mk(db, seed, "V2", "b", t + timedelta(minutes=120, seconds=1))
    assert candidate_pairs(db, seed["agency"].id, window_minutes=120) == []


def test_reversed_timestamps_no_pair(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t + timedelta(minutes=30))
    _mk(db, seed, "V2", "b", t)
    pairs = candidate_pairs(db, seed["agency"].id, window_minutes=120)
    assert len(pairs) == 1 and pairs[0]["a"].vehicle_id != pairs[0]["b"].vehicle_id
    # ordering is chronological regardless of insertion order
    assert pairs[0]["gap_minutes"] == 30.0


def test_same_nearmiss_never_pairs_with_itself(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t)
    assert candidate_pairs(db, seed["agency"].id) == []


def test_missing_route_uses_noroute_signature(db, seed):
    t = datetime.now(timezone.utc)
    a = _mk(db, seed, "V1", "a", t)
    b = _mk(db, seed, "V2", "b", t + timedelta(minutes=10))
    a.route_id = None
    b.route_id = None
    db.commit()
    chains = detect_chains(db, seed["agency"].id)
    assert len(chains) == 1 and chains[0]["key"].startswith("noroute|")


def test_since_until_windows_filter(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t - timedelta(days=5))
    _mk(db, seed, "V2", "b", t - timedelta(days=5) + timedelta(minutes=10))
    _mk(db, seed, "V3", "c", t)
    _mk(db, seed, "V4", "d", t + timedelta(minutes=10))
    old = detect_chains(db, seed["agency"].id, since=t - timedelta(days=6), until=t - timedelta(days=4))
    new = detect_chains(db, seed["agency"].id, since=t - timedelta(hours=1))
    assert len(old) == 1 and len(new) == 1
    # before/after occurrence counts support honest verification comparisons
    assert old[0]["occurrences"] == 1 and new[0]["occurrences"] == 1


def test_sparse_evidence_chain_still_returned(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t)
    _mk(db, seed, "V2", "b", t + timedelta(minutes=10))
    from backend.app.db.models.pattern import Pattern, NearMissPattern
    p = Pattern(agency_id=seed["agency"].id, route_id=seed["route"].id, pattern_type="T",
                title="t", recurrence_count=2, first_seen_at=t, last_seen_at=t, features={})
    db.add(p)
    db.commit()
    from backend.app.services.chains.chain_detector import pattern_chains
    for nm in db.query(NearMiss).all():
        db.add(NearMissPattern(near_miss_id=nm.id, pattern_id=p.id))
    db.commit()
    chains, _ = pattern_chains(db, p.id)
    assert len(chains) == 1 and chains[0]["evidence_ids"] == []  # honest: no evidence, still shown
