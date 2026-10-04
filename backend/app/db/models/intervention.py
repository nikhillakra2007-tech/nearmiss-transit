from __future__ import annotations
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import JSONVariant, Base, new_uuid


class Intervention(Base):
    __tablename__ = "interventions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    recommendation_id: Mapped[str] = mapped_column(ForeignKey("recommendations.id"), index=True)
    intervention_type: Mapped[str] = mapped_column(String(64))
    target: Mapped[str] = mapped_column(String(512))
    requested_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_status: Mapped[str] = mapped_column(String(32), default="PROPOSED")
    execution_result: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
