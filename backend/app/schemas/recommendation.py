from __future__ import annotations
from pydantic import BaseModel


class RecommendationRead(BaseModel):
    id: str
    title: str
    recommendation_type: str
    confidence_score: float
    status: str
