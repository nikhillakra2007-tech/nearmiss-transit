from backend.app.services.ingestion.gtfs_parser import parse_fixture_dicts
from backend.app.services.ingestion.normalizer import normalize
from backend.tests.fixtures.gtfs_fixtures import (VALID_ROWS, MALFORMED_ROWS, MISSING_TRIP_ROWS, DUPLICATE_ROWS, STALE_ROWS, ALERT_ROWS)
from backend.app.services.ingestion.ingestion_service import persist_normalized


def test_valid_normalizes():
    rows = parse_fixture_dicts(VALID_ROWS)
    n = normalize(rows[0], "demo")
    assert n.event_type == "VEHICLE_POSITION" and n.source_event_id


def test_malformed_does_not_crash():
    rows = parse_fixture_dicts(MALFORMED_ROWS)
    n = normalize(rows[0], "demo")
    assert n.event_type in ("VEHICLE_POSITION", "TRIP_UPDATE", "SERVICE_ALERT")


def test_missing_trip_ok():
    rows = parse_fixture_dicts(MISSING_TRIP_ROWS)
    assert normalize(rows[0], "demo").trip_external_id is None


def test_duplicate_deduped(db, seed):
    rows = parse_fixture_dicts(DUPLICATE_ROWS)
    normed = [normalize(r, "test-agency") for r in rows]
    res = persist_normalized(db, normed)
    assert res["ingested"] == 1 and res["duplicates"] == 1


def test_alert_maps_to_service_alert():
    rows = parse_fixture_dicts(ALERT_ROWS)
    assert normalize(rows[0], "demo").event_type == "SERVICE_ALERT"


def test_stale_accepted_with_timestamp(db, seed):
    rows = parse_fixture_dicts(STALE_ROWS)
    res = persist_normalized(db, [normalize(r, "test-agency") for r in rows])
    assert res["ingested"] == 1
