from __future__ import annotations
from pydantic import BaseModel


class InterventionCreate(BaseModel):
    recommendation_id: str
    intervention_type: str = "OPERATIONAL_REVIEW"
    target: str = ""


class InterventionRead(BaseModel):
    id: str
    execution_status: str
    target: str
