"""Detection loop: new events → vehicle state → near-miss (idempotent)."""
from __future__ import annotations
import asyncio
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.session import SessionLocal
from backend.app.services.detection.near_miss_detector import detect_for_vehicle

log = get_logger("detection_worker")


def detection_cycle() -> int:
    db = SessionLocal()
    try:
        vehicle_ids = [r[0] for r in db.query(TransitEvent.vehicle_id).filter(TransitEvent.vehicle_id.is_not(None)).distinct().all()]
        count = 0
        for vid in vehicle_ids:
            agency = db.query(TransitEvent.agency_id).filter_by(vehicle_id=vid).first()
            if detect_for_vehicle(db, vid, agency[0] if agency else ""):
                count += 1
        return count
    finally:
        db.close()


async def run_forever():
    while True:
        try:
            await asyncio.to_thread(detection_cycle)
        except Exception as exc:
            log.warning(f"detection_loop_error: {exc}")
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)
