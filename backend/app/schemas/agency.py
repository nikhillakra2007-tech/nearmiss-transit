from __future__ import annotations
from pydantic import BaseModel


class AgencyCreate(BaseModel):
    external_id: str
    name: str
    timezone: str = "UTC"
    source_url: str | None = None
    gtfs_static_url: str | None = None
    gtfs_realtime_url: str | None = None


class AgencyRead(AgencyCreate):
    id: str
