from __future__ import annotations
from pydantic import BaseModel


class VerificationRead(BaseModel):
    id: str
    intervention_id: str
    outcome: str
    confidence_score: float
    explanation: str = ""
