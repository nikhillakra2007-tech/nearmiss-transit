"""Normalizer: GTFS dicts → NormalizedTransitEvent (protobuf never leaks further)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class NormalizedTransitEvent:
    agency_external_id: str
    event_type: str
    observed_at: datetime
    scheduled_at: datetime | None = None
    delay_seconds: int | None = None
    route_external_id: str | None = None
    trip_external_id: str | None = None
    vehicle_external_id: str | None = None
    stop_external_id: str | None = None
    lat: float | None = None
    lon: float | None = None
    source_event_id: str = ""
    raw: dict = field(default_factory=dict)


def normalize(entity: dict, agency_external_id: str, scheduled_lookup=None) -> NormalizedTransitEvent:
    ts = int(entity.get("timestamp") or entity.get("feed_timestamp") or 0)
    observed = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else datetime.now(timezone.utc)
    kind = entity.get("kind", "vehicle")
    mapping = {"vehicle": "VEHICLE_POSITION", "trip_update": "TRIP_UPDATE", "alert": "SERVICE_ALERT"}
    etype = mapping.get(kind, "VEHICLE_POSITION")
    delay = None
    stop_updates = entity.get("stop_updates") or []
    if stop_updates:
        for s in stop_updates:
            if s.get("arrival_delay") is not None:
                delay = int(s["arrival_delay"])
                break
    if delay is None and entity.get("delay_seconds") is not None:
        delay = int(entity["delay_seconds"])
    elif delay is None and entity.get("delay") is not None:
        delay = int(entity["delay"])
    scheduled = None
    if scheduled_lookup and delay is not None:
        scheduled = scheduled_lookup(entity)
    eid = f"{entity.get('entity_id','e')}:{ts}:{entity.get('trip_id','')}:{entity.get('vehicle_id','')}"
    return NormalizedTransitEvent(
        agency_external_id=agency_external_id, event_type=etype, observed_at=observed,
        scheduled_at=scheduled, delay_seconds=delay,
        route_external_id=entity.get("route_id"), trip_external_id=entity.get("trip_id"),
        vehicle_external_id=entity.get("vehicle_id"), stop_external_id=entity.get("stop_id"),
        lat=entity.get("lat"), lon=entity.get("lon"), source_event_id=eid, raw=dict(entity))
