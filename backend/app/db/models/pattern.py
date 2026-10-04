from __future__ import annotations
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import JSONVariant, Base, new_uuid


class Pattern(Base):
    __tablename__ = "patterns"
    __table_args__ = (Index("ix_pattern_status", "status"), Index("ix_pattern_last_seen", "last_seen_at"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id"), index=True)
    route_id: Mapped[str | None] = mapped_column(ForeignKey("routes.id"), nullable=True, index=True)
    pattern_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str] = mapped_column(String(2048), default="")
    recurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    features: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NearMissPattern(Base):
    __tablename__ = "near_miss_patterns"
    __table_args__ = (UniqueConstraint("near_miss_id", "pattern_id", name="uq_nm_pattern"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    near_miss_id: Mapped[str] = mapped_column(ForeignKey("near_misses.id"), index=True)
    pattern_id: Mapped[str] = mapped_column(ForeignKey("patterns.id"), index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
