"""Forecast explanation: agent narrates a deterministic forecast result.

FACT/INFERENCE/HYPOTHESIS only — SIMULATION explicitly excluded here.
Extended bans: will fail, guarantee, unsafe, dangerous, accident.
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.exceptions import AgentOutputRejectedError
from backend.app.core.logging import get_logger
from backend.app.services.agent.provider import get_provider
from backend.app.services.agent.safety import validate_safe_output

log = get_logger("forecast_agent")
EXTRA_BANS = ("will fail", "will disrupt", "guarantee", "unsafe", "dangerous", "accident")


def explain_forecast(db: Session, result: dict) -> dict:
    evs = [{"id": i, "type": "EVIDENCE", "description": "supporting evidence record"}
           for i in result.get("evidence_ids", [])]
    bundle = {"forecast": {k: result[k] for k in
                           ("score", "status", "evaluated_at", "signals") if k in result},
              "evidence": evs}
    raw = get_provider().generate(bundle)
    raw["claims"] = [c for c in raw.get("claims", []) if c.get("type") in ("FACT", "INFERENCE", "HYPOTHESIS")]
    valid = {i for i in result.get("evidence_ids", [])}
    validated = validate_safe_output(raw, valid, extra_texts=[
        raw.get("summary", ""),
        ((raw.get("recommendation", {}) or {}).get("description", ""))])
    for phrase in EXTRA_BANS:
        rec = validated.get("recommendation", {}) or {}
        blob = (validated["summary"] + " " + rec.get("description", "") + " " +
                rec.get("expected_effect", "") + " " +
                " ".join(c.get("statement", "") for c in validated["claims"])).lower()
        if phrase in blob:
            raise AgentOutputRejectedError(f"forecast language rejected: {phrase}")
    log.info("forecast_explained")
    return validated
