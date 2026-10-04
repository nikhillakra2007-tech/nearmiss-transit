"""Investigation loop: new patterns → investigation → agent → recommendation."""
from __future__ import annotations
import asyncio
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.db.models.pattern import Pattern
from backend.app.db.session import SessionLocal
from backend.app.services.agent.orchestrator import investigate_with_agent
from backend.app.services.investigation.investigator import open_investigation
from backend.app.services.patterns.pattern_detector import detect_patterns

log = get_logger("investigation_worker")


def investigation_cycle() -> int:
    db = SessionLocal()
    try:
        patterns = detect_patterns(db)
        done = 0
        for p in db.query(Pattern).filter_by(status="OPEN").all():
            inv = open_investigation(db, p.id)
            investigate_with_agent(db, inv.id, p.id)
            p.status = "INVESTIGATED"
            db.commit()
            done += 1
        return done
    finally:
        db.close()


async def run_forever():
    while True:
        try:
            await asyncio.to_thread(investigation_cycle)
        except Exception as exc:
            log.warning(f"investigation_loop_error: {exc}")
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS * 4)
