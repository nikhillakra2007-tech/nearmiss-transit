"""Evidence builder: every conclusion points to stored rows."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.db.models.investigation import Evidence
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern
from backend.app.db.models.transit_event import TransitEvent
from backend.app.db.models.service_alert import ServiceAlert


def build_evidence(db: Session, investigation_id: str, pattern_id: str) -> list[Evidence]:
    links = db.query(NearMissPattern).filter_by(pattern_id=pattern_id).all()
    out: list[Evidence] = []
    for link in links:
        nm = db.get(NearMiss, link.near_miss_id)
        if not nm:
            continue
        start = db.get(TransitEvent, nm.start_event_id)
        out.append(Evidence(investigation_id=investigation_id, evidence_type="NEAR_MISS",
                            source_entity_type="near_miss", source_entity_id=nm.id,
                            description=f"Near-miss {nm.near_miss_type} peak {(nm.abnormal_value or {}).get('peak_delay')}",
                            observed_at=nm.detected_at,
                            payload={"peak": (nm.abnormal_value or {}).get("peak_delay"),
                                     "baseline": nm.baseline_value}, confidence_score=nm.confidence_score))
        if start:
            out.append(Evidence(investigation_id=investigation_id, evidence_type="EVENT",
                                source_entity_type="transit_event", source_entity_id=start.id,
                                description=f"Start event delay={start.delay_seconds}s",
                                observed_at=start.observed_at,
                                payload={"delay": start.delay_seconds}, confidence_score=0.9))
    for alert in db.query(ServiceAlert).limit(25).all():
        out.append(Evidence(investigation_id=investigation_id, evidence_type="ALERT",
                            source_entity_type="service_alert", source_entity_id=alert.id,
                            description=f"Alert: {alert.header}", observed_at=alert.active_from,
                            payload={"severity": alert.severity}, confidence_score=0.7))
    for e in out:
        db.add(e)
    db.commit()
    return out
