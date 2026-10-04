from __future__ import annotations
import enum
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import JSONVariant, Base, new_uuid


class NearMissStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    ACTION_RECOMMENDED = "ACTION_RECOMMENDED"
    RESOLVED = "RESOLVED"


class NearMiss(Base):
    __tablename__ = "near_misses"
    __table_args__ = (Index("ix_nm_status", "status"), Index("ix_nm_route_detected", "route_id", "detected_at"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id"), index=True)
    route_id: Mapped[str | None] = mapped_column(ForeignKey("routes.id"), nullable=True, index=True)
    trip_id: Mapped[str | None] = mapped_column(ForeignKey("trips.id"), nullable=True)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    start_event_id: Mapped[str] = mapped_column(ForeignKey("transit_events.id"))
    recovery_event_id: Mapped[str | None] = mapped_column(ForeignKey("transit_events.id"), nullable=True)
    detected_at: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    near_miss_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM")
    baseline_value: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    abnormal_value: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    recovery_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(32), default="DETECTED", index=True)
    detection_reason: Mapped[str] = mapped_column(String(2048), default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
