"""FastAPI dependencies: DB session + pagination."""
from __future__ import annotations
from fastapi import Query
from backend.app.db.session import get_session

get_db = get_session


def pagination(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return {"limit": limit, "offset": offset}
