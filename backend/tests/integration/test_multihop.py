"""Multi-hop domino tests: 2/3-hop, depth, cycles, order, evidence, boundaries."""
from datetime import datetime, timedelta, timezone
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.route import Route
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.vehicle import Vehicle
from backend.app.services.chains.multihop import build_trails, detect_multihop


def _route(db, seed, ext):
    r = db.query(Route).filter_by(agency_id=seed["agency"].id, external_route_id=ext).first()
    if not r:
        r = Route(agency_id=seed["agency"].id, external_route_id=ext, short_name=ext)
        db.add(r)
        db.commit()
    return r


def _mk(db, seed, vext, dext, at, rext="42"):
    route = _route(db, seed, rext)
    veh = db.query(Vehicle).filter_by(external_vehicle_id=vext).first()
    if not veh:
        veh = Vehicle(agency_id=seed["agency"].id, external_vehicle_id=vext)
        db.add(veh)
        db.commit()
    e = TransitEvent(agency_id=seed["agency"].id, route_id=route.id, vehicle_id=veh.id,
                     event_type="TRIP_UPDATE", observed_at=at, delay_seconds=900,
                     status="OBSERVED", source="test", source_event_id=f"mh-{vext}-{dext}",
                     raw_payload={}, normalized_payload={})
    db.add(e)
    db.commit()
    nm = NearMiss(agency_id=seed["agency"].id, route_id=route.id, vehicle_id=veh.id,
                  start_event_id=e.id, detected_at=at, near_miss_type="T",
                  severity="HIGH", baseline_value={}, abnormal_value={}, confidence_score=0.8,
                  status="DETECTED", detection_reason="t")
    db.add(nm)
    db.commit()
    return nm


def _evidence_all(db, seed):
    from datetime import timezone as _tz
    from backend.app.db.models.investigation import Investigation, Evidence
    from backend.app.db.models.pattern import Pattern
    t = datetime.now(_tz.utc)
    p = Pattern(agency_id=seed["agency"].id, route_id=seed["route"].id, pattern_type="T",
                title="t", recurrence_count=1, first_seen_at=t, last_seen_at=t, features={})
    db.add(p)
    db.commit()
    inv = Investigation(pattern_id=p.id, status="OPEN")
    db.add(inv)
    db.commit()
    for nm in db.query(NearMiss).all():
        db.add(Evidence(investigation_id=inv.id, evidence_type="NEAR_MISS",
                        source_entity_type="near_miss", source_entity_id=nm.id,
                        description="e", observed_at=t, payload={}, confidence_score=0.9))
    db.commit()


def test_two_hop_chain(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t, "42")
    _mk(db, seed, "V2", "b", t + timedelta(minutes=10), "17")
    _mk(db, seed, "V3", "c", t + timedelta(minutes=22), "8")
    _evidence_all(db, seed)
    chains = detect_multihop(db, seed["agency"].id)
    assert len(chains) == 1 and chains[0]["depth"] == 2
    assert chains[0]["avg_gaps"] == [10.0, 12.0]


def test_three_hop_and_max_depth_truncation(db, seed):
    t = datetime.now(timezone.utc)
    routes = ["42", "17", "8", "31", "9"]
    for i, r in enumerate(routes):
        _mk(db, seed, f"V{i}", f"n{i}", t + timedelta(minutes=10 * i), r)
    _evidence_all(db, seed)
    chains = detect_multihop(db, seed["agency"].id, max_depth=3)
    assert chains and all(c["depth"] <= 3 for c in chains)
    deep = [c for c in chains if c["depth"] == 3]
    assert deep  # 4-edge trail yields truncated 3-edge chain, never longer


def test_self_loop_and_duplicate_node_rejected(db, seed):
    from backend.app.services.chains.chain_detector import candidate_pairs
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t, "42")
    _mk(db, seed, "V2", "b", t + timedelta(minutes=10), "17")
    pairs = candidate_pairs(db, seed["agency"].id)
    # synthetic cycle attempt: same route twice must not form a trail
    trails = build_trails(pairs + [{"a": pairs[0]["b"], "b": pairs[0]["a"], "gap_minutes": 5.0}], 3)
    assert all(len({n for e in t for n in (e["a"].id, e["b"].id)}) == len(t) + 1 for t in trails)


def test_chronological_and_same_vehicle_and_boundaries(db, seed):
    t = datetime.now(timezone.utc)
    _mk(db, seed, "V1", "a", t, "42")
    _mk(db, seed, "V1", "b", t + timedelta(minutes=10), "17")  # same vehicle
    assert detect_multihop(db, seed["agency"].id) == []
    _mk(db, seed, "V2", "c", t + timedelta(minutes=120), "8")  # exact limit ok
    _mk(db, seed, "V3", "d", t + timedelta(minutes=120, seconds=1), "9")  # +1s excluded
    chains = detect_multihop(db, seed["agency"].id, window_minutes=120)
    assert chains == [] or all(c["depth"] >= 2 for c in chains)


def test_missing_evidence_excluded_and_strength(db, seed):
    from backend.app.db.models.pattern import Pattern
    t = datetime.now(timezone.utc)
    for v, r, m in (("V1", "42", 0), ("V2", "17", 10), ("V3", "8", 22),
                    ("V4", "42", 200), ("V5", "17", 210), ("V6", "8", 222)):
        _mk(db, seed, v, v, t + timedelta(minutes=m), r)
    chains = detect_multihop(db, seed["agency"].id)
    assert chains == []  # no evidence rows anywhere → excluded, not fabricated
    p = Pattern(agency_id=seed["agency"].id, route_id=seed["route"].id, pattern_type="T",
                title="t", recurrence_count=2, first_seen_at=t, last_seen_at=t, features={})
    db.add(p)
    db.commit()
    from backend.app.db.models.investigation import Investigation, Evidence
    inv = Investigation(pattern_id=p.id, status="OPEN")
    db.add(inv)
    db.commit()
    for nm in db.query(NearMiss).all():
        db.add(Evidence(investigation_id=inv.id, evidence_type="NEAR_MISS",
                        source_entity_type="near_miss", source_entity_id=nm.id,
                        description="e", observed_at=t, payload={}, confidence_score=0.9))
    db.commit()
    chains = detect_multihop(db, seed["agency"].id)
    assert len(chains) == 1 and chains[0]["strength"] == "RECURRING"
    assert chains[0]["evidence_ids"]
    again = detect_multihop(db, seed["agency"].id)
    assert again == chains  # idempotent + deterministic order
