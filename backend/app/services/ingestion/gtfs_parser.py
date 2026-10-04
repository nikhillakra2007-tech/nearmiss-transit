"""GTFS-RT protobuf parser → plain dicts. Never crashes whole cycle on one bad entity."""
from __future__ import annotations
from datetime import datetime, timezone
from backend.app.core.exceptions import FeedParseError
from backend.app.core.logging import get_logger

log = get_logger("gtfs_parser")


def parse_feed(raw: bytes) -> list[dict]:
    """Try real protobuf decode; fall back to raising FeedParseError on garbage."""
    try:
        from google.transit import gtfs_realtime_pb2
    except Exception:
        raise FeedParseError("gtfs-realtime-bindings not installed")
    msg = gtfs_realtime_pb2.FeedMessage()
    try:
        msg.ParseFromString(raw)
    except Exception as exc:
        raise FeedParseError(f"protobuf decode failed: {exc}")
    out: list[dict] = []
    feed_ts = int(getattr(msg.header, "timestamp", 0) or 0)
    for entity in msg.entity:
        try:
            out.append(_entity_to_dict(entity, feed_ts))
        except Exception as exc:
            log.warning(f"skip malformed entity {entity.id}: {exc}")
    return out


def _entity_to_dict(entity, feed_ts: int) -> dict:
    base = {"entity_id": entity.id, "feed_timestamp": feed_ts}
    if entity.HasField("vehicle"):
        v = entity.vehicle
        base.update({"kind": "vehicle", "vehicle_id": v.vehicle.id or v.vehicle.label or entity.id,
                     "trip_id": v.trip.trip_id or None, "route_id": v.trip.route_id or None,
                     "lat": v.position.latitude or None, "lon": v.position.longitude or None,
                     "timestamp": int(v.timestamp or feed_ts)})
    elif entity.HasField("trip_update"):
        tu = entity.trip_update
        base.update({"kind": "trip_update", "trip_id": tu.trip.trip_id or None,
                     "route_id": tu.trip.route_id or None, "vehicle_id": tu.vehicle.id or None,
                     "timestamp": int(tu.timestamp or feed_ts),
                     "stop_updates": [{"stop_id": s.stop_id, "arrival_delay": s.arrival.delay if s.HasField("arrival") else None,
                                        "departure_delay": s.departure.delay if s.HasField("departure") else None} for s in tu.stop_time_update]})
    elif entity.HasField("alert"):
        a = entity.alert
        base.update({"kind": "alert", "header": a.header_text.translation[0].text if a.header_text.translation else "",
                     "description": a.description_text.translation[0].text if a.description_text.translation else "",
                     "timestamp": feed_ts})
    else:
        base.update({"kind": "unknown", "timestamp": feed_ts})
    return base


def parse_fixture_dicts(rows: list[dict]) -> list[dict]:
    """Test/demo path: accept already-dict rows (derived from real feed structure)."""
    now = int(datetime.now(timezone.utc).timestamp())
    out = []
    for r in rows:
        d = dict(r)
        d.setdefault("timestamp", now)
        d.setdefault("kind", "vehicle")
        out.append(d)
    return out
