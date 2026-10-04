from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class NearMissRead(BaseModel):
    id: str
    agency_id: str
    near_miss_type: str
    severity: str
    status: str
    confidence_score: float
    detected_at: datetime
    recovery_duration_seconds: int | None = None
    detection_reason: str = ""
