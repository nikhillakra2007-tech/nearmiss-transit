from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class EventRead(BaseModel):
    id: str
    agency_id: str
    event_type: str
    observed_at: datetime
    delay_seconds: int | None = None
    route_id: str | None = None
    trip_id: str | None = None
    vehicle_id: str | None = None
    stop_id: str | None = None
    source_event_id: str
