"""Chain agent: deterministic bundle in, validated claims out.

Same provider abstraction + output schema as investigations. Extra guard:
causal-certainty language ("caused", "proves", ...) is rejected — MAY means MAY.
Result is ephemeral (returned, not persisted): no table represents a
chain recommendation, and inventing persistence would fake the record.
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.exceptions import AgentOutputRejectedError
from backend.app.core.logging import get_logger
from backend.app.db.models.investigation import Evidence
from backend.app.services.agent.planner import validate_agent_output
from backend.app.services.agent.provider import get_provider
from backend.app.services.chains.chain_detector import pattern_chains

log = get_logger("chain_agent")

import re as _re

BANNED_CAUSAL = ("caused", "causes", "cause", "causal", "caused by", "proof", "proves", "proven",
                 "definitely", "certainly", "undoubtedly")
_BANNED_RX = _re.compile(r"\b(" + "|".join(map(_re.escape, BANNED_CAUSAL)) + r")\b")


def _banned_hit(text: str) -> str | None:
    m = _BANNED_RX.search(text.lower())
    return m.group(0) if m else None


def validate_chain_output(output: dict, valid_ids: set[str]) -> dict:
    validated = validate_agent_output(output, valid_ids)
    for claim in validated["claims"]:
        hit = _banned_hit(claim.get("statement", ""))
        if hit:
            raise AgentOutputRejectedError(f"causal-certainty language rejected: {hit}")
    rec_text = (validated.get("recommendation", {}).get("description", "") + " " +
                validated.get("recommendation", {}).get("expected_effect", ""))
    for banned in ("will fix", "guaranteed"):
        if banned in rec_text.lower():
            raise AgentOutputRejectedError(f"causal-certainty language rejected: {banned}")
    hit = _banned_hit(rec_text)
    if hit:
        raise AgentOutputRejectedError(f"causal-certainty language rejected: {hit}")
    return validated


def investigate_chain(db: Session, pattern_id: str, chain_key: str,
                      since=None, until=None, window_minutes=None) -> dict:
    chains, _ = pattern_chains(db, pattern_id, since, until, window_minutes)
    chain = next((c for c in chains if c["key"] == chain_key), None)
    if not chain:
        from backend.app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError(f"chain {chain_key} not found for pattern")
    evs = db.query(Evidence).filter(Evidence.id.in_(chain["evidence_ids"])).all() if chain["evidence_ids"] else []
    bundle = {"pattern": {"id": pattern_id}, "chain": {k: chain[k] for k in
              ("key", "source_route_id", "source_type", "target_route_id", "target_type",
               "relationship", "strength", "occurrences", "avg_gap_minutes", "pairs")},
              "evidence": [{"id": e.id, "type": e.evidence_type, "description": e.description} for e in evs]}
    raw = get_provider().generate(bundle)
    validated = validate_chain_output(raw, {e.id for e in evs} | {e["id"] for e in bundle["evidence"]})
    log.info(f"chain_investigated pattern={pattern_id} key={chain_key}")
    return {"chain": chain, "agent": validated}
