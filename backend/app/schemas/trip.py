from __future__ import annotations
from datetime import date
from pydantic import BaseModel


class TripCreate(BaseModel):
    route_id: str
    external_trip_id: str
    service_date: date | None = None
    direction_id: int | None = None
    start_time: str | None = None


class TripRead(TripCreate):
    id: str
