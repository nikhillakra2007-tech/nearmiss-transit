"""GTFS fixtures: valid / malformed / missing fields / duplicate / stale / alert."""
VALID_ROWS = [{"entity_id": "veh1", "kind": "vehicle", "trip_id": "T100", "route_id": "42",
               "vehicle_id": "V100", "lat": 12.97, "lon": 77.59, "timestamp": 1700000000}]
MALFORMED_ROWS = [{"entity_id": "bad1"}]
MISSING_TRIP_ROWS = [{"entity_id": "v2", "kind": "vehicle", "vehicle_id": "V2", "timestamp": 1700000000}]
DUPLICATE_ROWS = VALID_ROWS + VALID_ROWS
STALE_ROWS = [{"entity_id": "old", "kind": "vehicle", "vehicle_id": "V9", "timestamp": 1000000000}]
ALERT_ROWS = [{"entity_id": "a1", "kind": "alert", "header": "Line blocked", "description": "detour", "timestamp": 1700000000}]
