"""Generic repository helpers (parameterized SQLAlchemy only, no raw SQL)."""
from __future__ import annotations
from sqlalchemy.orm import Session


class BaseRepository:
    model = None

    def __init__(self, db: Session):
        self.db = db

    def get(self, id: str):
        return self.db.get(self.model, id)

    def list(self, limit: int = 50, offset: int = 0):
        q = self.db.query(self.model).order_by(self.model.created_at.desc()) if hasattr(self.model, "created_at") else self.db.query(self.model)
        return q.offset(offset).limit(min(max(limit, 1), 200)).all()

    def add(self, obj):
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
