"""Lightweight asyncio worker loops (no Celery). Each independently testable + idempotent."""
from __future__ import annotations
import asyncio
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.db.session import SessionLocal
from backend.app.services.ingestion.gtfs_client import fetch_feed
from backend.app.services.ingestion.gtfs_parser import parse_feed
from backend.app.services.ingestion.normalizer import normalize
from backend.app.services.ingestion.ingestion_service import persist_normalized

log = get_logger("ingestion_worker")


async def ingestion_cycle(agency_external_id: str = "demo-agency") -> dict:
    raw = await fetch_feed()
    rows = await asyncio.to_thread(parse_feed, raw)
    normalized = [normalize(r, agency_external_id) for r in rows]
    db: Session = SessionLocal()
    try:
        return await asyncio.to_thread(persist_normalized, db, normalized)
    finally:
        db.close()


async def run_forever(agency_external_id: str = "demo-agency"):
    while True:
        try:
            await ingestion_cycle(agency_external_id)
        except Exception as exc:
            log.warning(f"ingestion_loop_error: {exc}")
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
