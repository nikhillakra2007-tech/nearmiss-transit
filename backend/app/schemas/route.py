from __future__ import annotations
from pydantic import BaseModel


class RouteCreate(BaseModel):
    agency_id: str
    external_route_id: str
    short_name: str | None = None
    long_name: str | None = None
    route_type: str | None = None


class RouteRead(RouteCreate):
    id: str
