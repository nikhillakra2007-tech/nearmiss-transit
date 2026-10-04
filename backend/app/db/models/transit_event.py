from __future__ import annotations
import enum
from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import JSONVariant, Base, new_uuid


class EventType(str, enum.Enum):
    VEHICLE_POSITION = "VEHICLE_POSITION"
    TRIP_UPDATE = "TRIP_UPDATE"
    ARRIVAL = "ARRIVAL"
    DEPARTURE = "DEPARTURE"
    DELAY = "DELAY"
    CANCELLATION = "CANCELLATION"
    SERVICE_ALERT = "SERVICE_ALERT"
    ROUTE_DEVIATION = "ROUTE_DEVIATION"
    RECOVERY = "RECOVERY"
    INGESTION_ERROR = "INGESTION_ERROR"


class TransitEvent(Base):
    __tablename__ = "transit_events"
    __table_args__ = (
        UniqueConstraint("agency_id", "source_event_id", name="uq_event_agency_source"),
        Index("ix_event_agency_observed", "agency_id", "observed_at"),
        Index("ix_event_route_observed", "route_id", "observed_at"),
        Index("ix_event_type_observed", "event_type", "observed_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    agency_id: Mapped[str] = mapped_column(ForeignKey("agencies.id"), index=True)
    route_id: Mapped[str | None] = mapped_column(ForeignKey("routes.id"), nullable=True, index=True)
    trip_id: Mapped[str | None] = mapped_column(ForeignKey("trips.id"), nullable=True, index=True)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    stop_id: Mapped[str | None] = mapped_column(ForeignKey("stops.id"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    observed_at: Mapped[object] = mapped_column(DateTime(timezone=True), index=True)
    scheduled_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delay_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OBSERVED")
    source: Mapped[str] = mapped_column(String(32), default="gtfs-rt")
    source_event_id: Mapped[str] = mapped_column(String(256), index=True)
    raw_payload: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    normalized_payload: Mapped[dict] = mapped_column(JSONVariant, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
