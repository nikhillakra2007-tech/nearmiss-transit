"""Shared agent-output safety: evidence membership + banned-language containment.

Applies to chain + simulation explanations. Banned language covers causal
certainty, guaranteed prevention, and safety/failure-probability claims.
"""
from __future__ import annotations
import re
from backend.app.core.exceptions import AgentOutputRejectedError
from backend.app.services.agent.planner import validate_agent_output

BANNED = ("caused", "causes", "cause", "causal", "caused by", "proof", "proves",
          "proven", "definitely", "certainly", "undoubtedly", "will fix",
          "will fail", "will disrupt", "will prevent", "guarantee", "guarantees",
          "guaranteed", "accident", "accident risk", "unsafe", "dangerous",
          "safety score", "failure probability", "100% certain", "100 percent certain")
_RX = re.compile(r"\b(" + "|".join(map(re.escape, BANNED)) + r")\b")


def check_text(text: str) -> None:
    m = _RX.search((text or "").lower())
    if m:
        raise AgentOutputRejectedError(f"unsupported claim language rejected: {m.group(0)}")


def validate_safe_output(output: dict, valid_ids: set[str],
                         extra_texts: list[str] | None = None) -> dict:
    validated = validate_agent_output(output, valid_ids)
    for claim in validated["claims"]:
        check_text(claim.get("statement", ""))
    rec = validated.get("recommendation", {}) or {}
    check_text(rec.get("description", "") + " " + rec.get("expected_effect", ""))
    for t in extra_texts or []:
        check_text(t)
    return validated
