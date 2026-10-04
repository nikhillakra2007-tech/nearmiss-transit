"""SQLAlchemy base + JSONB-variant (JSONB on Postgres, JSON elsewhere) + UUID helper."""
from __future__ import annotations

import uuid

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase

JSONVariant = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


def new_uuid() -> str:
    return str(uuid.uuid4())
