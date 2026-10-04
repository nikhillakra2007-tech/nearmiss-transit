"""Causal analysis: hypotheses only — edges are MAY_CONTRIBUTE_TO, never proven facts."""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.db.models.investigation import CausalEdge, Evidence


def propose_edges(db: Session, investigation_id: str) -> list[CausalEdge]:
    evs = db.query(Evidence).filter_by(investigation_id=investigation_id).all()
    alerts = [e for e in evs if e.evidence_type == "ALERT"]
    nms = [e for e in evs if e.evidence_type == "NEAR_MISS"]
    edges = []
    for a in alerts:
        for n in nms:
            edges.append(CausalEdge(investigation_id=investigation_id, source_evidence_id=a.id,
                                    target_evidence_id=n.id, relationship_type="MAY_CONTRIBUTE_TO",
                                    confidence_score=0.45,
                                    explanation="Hypothesis: alert window overlaps near-miss; not proven."))
    for e in edges:
        db.add(e)
    db.commit()
    return edges
