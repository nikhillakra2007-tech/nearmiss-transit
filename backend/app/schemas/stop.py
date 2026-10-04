from __future__ import annotations
from pydantic import BaseModel


class StopCreate(BaseModel):
    agency_id: str
    external_stop_id: str
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class StopRead(StopCreate):
    id: str
