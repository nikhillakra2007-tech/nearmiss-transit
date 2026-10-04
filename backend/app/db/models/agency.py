from __future__ import annotations
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base, new_uuid


class Agency(Base):
    __tablename__ = "agencies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    source_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gtfs_static_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gtfs_realtime_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
