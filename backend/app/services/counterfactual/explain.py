"""Simulation explanation: agent narrates a counterfactual result.

Claim types FACT (observed) / SIMULATION (transformed) / INFERENCE / HYPOTHESIS.
SIMULATION claims must cite the near-miss evidence and never present the
transformation as an observed fact or a prevented failure.
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.logging import get_logger
from backend.app.db.models.investigation import Evidence
from backend.app.services.agent.provider import get_provider
from backend.app.services.agent.safety import validate_safe_output
from backend.app.services.counterfactual.lab import simulate_near_miss

log = get_logger("simulation_agent")

ALLOWED_TYPES = ("FACT", "SIMULATION", "INFERENCE", "HYPOTHESIS")


def explain_simulation(db: Session, near_miss_id: str, sim: dict) -> dict:
    from backend.app.db.models.near_miss import NearMiss
    nm = db.get(NearMiss, near_miss_id)
    evs = []
    if nm:
        evs = db.query(Evidence).filter_by(source_entity_type="near_miss",
                                           source_entity_id=near_miss_id).all()
    bundle = {"near_miss": near_miss_id, "scenario": sim.get("scenario"),
              "parameter": sim.get("parameter"), "original": sim.get("original"),
              "simulated": sim.get("simulated"), "delta": sim.get("delta"),
              "evidence": [{"id": e.id, "type": e.evidence_type,
                             "description": e.description} for e in evs]}
    raw = get_provider().generate(bundle)
    # Constrain to allowed claim vocabulary (provider is generic).
    claims = [c for c in raw.get("claims", []) if c.get("type") in ALLOWED_TYPES]
    if sim.get("simulated") and not any(c.get("type") == "SIMULATION" for c in claims):
        eids = [e["id"] for e in bundle["evidence"][:2]]
        claims.append({"type": "SIMULATION",
                       "statement": (f"Under scenario {sim['scenario']} the simulated peak is "
                                     f"{sim['simulated']['peak']} minutes versus observed "
                                     f"{sim['original']['peak']} minutes."),
                       "evidence_ids": eids, "confidence": 0.9})
    raw["claims"] = claims
    valid = {e.id for e in evs}
    validated = validate_safe_output(raw, valid)
    log.info(f"simulation_explained nm={near_miss_id}")
    return validated
