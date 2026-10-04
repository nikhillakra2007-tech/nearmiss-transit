"""Deterministic demo prep: seed -> detect -> patterns -> investigate -> report.
Idempotent: safe to rerun (seed skips dupes, detection/patterns/investigations
reuse existing rows). Honors DATABASE_URL (default: app sqlite file).
Usage: DATABASE_URL=sqlite:///./demo.db python scripts/prep_demo.py"""
import os
import runpy
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.db import models  # noqa


def main() -> dict:
    Base.metadata.create_all(bind=engine)
    runpy.run_path(os.path.join(os.path.dirname(__file__), "seed_demo.py"),
                   run_name="__main__")
    from backend.app.db.models.agency import Agency
    from backend.app.db.models.pattern import Pattern
    from backend.app.db.models.investigation import Investigation
    from backend.app.db.models.recommendation import Recommendation
    from backend.app.db.models.vehicle import Vehicle
    from backend.app.services.detection.near_miss_detector import detect_for_vehicle
    from backend.app.services.patterns.pattern_detector import detect_patterns
    from backend.app.services.investigation.investigator import open_investigation
    from backend.app.services.agent.orchestrator import investigate_with_agent
    db = SessionLocal()
    ag = db.query(Agency).filter_by(external_id="demo-agency").one()
    nms = [detect_for_vehicle(db, v.id, ag.id) for v in db.query(Vehicle).all()]
    pats = detect_patterns(db)
    report = {"near_misses": len([n for n in nms if n]), "patterns": []}
    for p in pats:
        inv = db.query(Investigation).filter_by(pattern_id=p.id).order_by(Investigation.created_at.desc()).first()
        if inv is None:
            inv = open_investigation(db, p.id)
        rec = db.query(Recommendation).filter_by(investigation_id=inv.id).first()
        if rec is None:
            rec_id = investigate_with_agent(db, inv.id, p.id)["recommendation_id"]
        else:
            rec_id = rec.id  # rerun-safe: reuse, don't duplicate agent work
        report["patterns"].append({"id": p.id, "title": p.title,
                                   "recurrence": p.recurrence_count,
                                   "investigation_id": inv.id, "recommendation_id": rec_id})
    db.close()
    print("DEMO READY:", report["near_misses"], "near-misses,",
          len(report["patterns"]), "patterns")
    for p in report["patterns"]:
        print(" pattern", p["id"], "| detail: /api/v1/patterns/" + p["id"] + "/detail",
              "| chains: /api/v1/patterns/" + p["id"] + "/chains")
    return report


if __name__ == "__main__":
    main()
