"""Provider abstraction — replaceable, mock by default. Deterministic facts never from LLM."""
from __future__ import annotations
from backend.app.core.config import settings


class AgentProvider:
    name = "base"

    def generate(self, bundle: dict) -> dict:
        raise NotImplementedError


class MockProvider(AgentProvider):
    name = "mock"

    def generate(self, bundle: dict) -> dict:
        evs = bundle.get("evidence", [])
        ids = [e["id"] for e in evs[:4]]
        claims = []
        if ids:
            claims.append({"type": "FACT", "statement": f"{len(evs)} evidence items reviewed; peak delays documented.", "evidence_ids": ids[:2], "confidence": 0.9})
            claims.append({"type": "INFERENCE", "statement": "Recurrence concentrates in the same route/time bucket.", "evidence_ids": ids[:2], "confidence": 0.7})
            claims.append({"type": "HYPOTHESIS", "statement": "A recurring dwell-time bottleneck may contribute (unproven).", "evidence_ids": ids[:1], "confidence": 0.45})
        return {"summary": f"Reviewed {len(evs)} evidence items for pattern {bundle.get('pattern', {}).get('id')}.",
                "claims": claims, "possible_causes": ["dwell-time bottleneck (hypothesis)"],
                "recommendation": {"title": "Increase operational observation during affected window",
                                    "description": "Monitor the affected route/stops during the recurring window and review schedule adherence.",
                                    "expected_effect": "Earlier detection of escalation; data for schedule review.",
                                    "confidence": 0.65}}


def get_provider(name: str | None = None) -> AgentProvider:
    pname = (name or settings.LLM_PROVIDER).lower()
    # Future: "groq"/"openai" providers read LLM_API_KEY/LLM_MODEL. Mock default keeps
    # the system functional with no LLM (spec rule 8).
    return MockProvider()
