from __future__ import annotations
from pydantic import BaseModel


class InvestigationRead(BaseModel):
    id: str
    pattern_id: str
    status: str
    investigation_summary: str = ""
    confidence_score: float = 0.0


class InvestigationCreate(BaseModel):
    pattern_id: str
