from __future__ import annotations
from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import JSONVariant, Base, new_uuid


class Verification(Base):
    __tablename__ = "verifications"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    intervention_id: Mapped[str] = mapped_column(ForeignKey("interventions.id"), index=True)
    verification_started_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    verification_ended_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    baseline_metrics: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    post_metrics: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    outcome: Mapped[str] = mapped_column(String(32), default="INSUFFICIENT_DATA")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str] = mapped_column(String(2048), default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
