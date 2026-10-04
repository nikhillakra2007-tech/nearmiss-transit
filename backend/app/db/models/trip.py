from __future__ import annotations
from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import JSONVariant, Base, new_uuid


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (UniqueConstraint("route_id", "external_trip_id", name="uq_trip_route_ext"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    route_id: Mapped[str] = mapped_column(ForeignKey("routes.id"), index=True)
    external_trip_id: Mapped[str] = mapped_column(String(128), index=True)
    service_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    direction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[str | None] = mapped_column(String(16), nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", JSONVariant, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
