"""Structured-output validation: reject hallucinated evidence IDs + malformed claims."""
from __future__ import annotations
from backend.app.core.exceptions import AgentOutputRejectedError

# V2.2 additive: SIMULATION claims describe hypothetical transformations
# (counterfactual lab). Same evidence rules apply; simulations are never facts.
CLAIM_TYPES = ("FACT", "INFERENCE", "HYPOTHESIS", "SIMULATION")


def validate_agent_output(output: dict, valid_evidence_ids: set[str]) -> dict:
    if not isinstance(output, dict):
        raise AgentOutputRejectedError("output must be an object")
    for field in ("summary", "claims", "recommendation"):
        if field not in output:
            raise AgentOutputRejectedError(f"missing field: {field}")
    if not isinstance(output["claims"], list):
        raise AgentOutputRejectedError("claims must be a list")
    for c in output["claims"]:
        if c.get("type") not in CLAIM_TYPES:
            raise AgentOutputRejectedError(f"bad claim type: {c.get('type')}")
        if not c.get("statement"):
            raise AgentOutputRejectedError("claim missing statement")
        eids = c.get("evidence_ids", [])
        if c["type"] == "FACT" and not eids:
            raise AgentOutputRejectedError("FACT needs evidence_ids")
        for eid in eids:
            if eid not in valid_evidence_ids:
                raise AgentOutputRejectedError(f"unknown evidence id: {eid}")
        cf = c.get("confidence", 0.5)
        if not (0.0 <= cf <= 1.0):
            raise AgentOutputRejectedError("confidence out of range")
    rec = output["recommendation"]
    for field in ("title", "description"):
        if not rec.get(field):
            raise AgentOutputRejectedError(f"recommendation missing {field}")
    return output
