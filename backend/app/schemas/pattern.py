from __future__ import annotations
from pydantic import BaseModel


class PatternRead(BaseModel):
    id: str
    title: str
    pattern_type: str
    recurrence_count: int
    severity: str
    status: str
    confidence_score: float
