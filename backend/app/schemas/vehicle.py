from __future__ import annotations
from pydantic import BaseModel


class VehicleCreate(BaseModel):
    agency_id: str
    external_vehicle_id: str
    label: str | None = None


class VehicleRead(VehicleCreate):
    id: str
