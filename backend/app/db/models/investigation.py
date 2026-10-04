from __future__ import annotations
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import JSONVariant, Base, new_uuid


class Investigation(Base):
    __tablename__ = "investigations"
    __table_args__ = (Index("ix_inv_status", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    pattern_id: Mapped[str] = mapped_column(ForeignKey("patterns.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    investigation_summary: Mapped[str] = mapped_column(String(4096), default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id"), index=True)
    evidence_type: Mapped[str] = mapped_column(String(64))
    source_entity_type: Mapped[str] = mapped_column(String(64))
    source_entity_id: Mapped[str] = mapped_column(String(36))
    description: Mapped[str] = mapped_column(String(2048))
    observed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CausalEdge(Base):
    __tablename__ = "causal_edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    investigation_id: Mapped[str] = mapped_column(ForeignKey("investigations.id"), index=True)
    source_evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id"))
    target_evidence_id: Mapped[str] = mapped_column(ForeignKey("evidence.id"))
    relationship_type: Mapped[str] = mapped_column(String(64), default="MAY_CONTRIBUTE_TO")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    explanation: Mapped[str] = mapped_column(String(2048), default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
