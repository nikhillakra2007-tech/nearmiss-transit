"""Intervention Sandbox — compare modeled interventions on observed data.

Reuses counterfactual transforms verbatim (no duplicated mathematics).
Improvement = mean(peak-fraction-gain, duration-fraction-gain), deterministic
ranking with name tiebreak. BEST MODELED INTERVENTION — never a real-world
guarantee. Recommendation reuses the existing service + PENDING handoff.
"""
from __future__ import annotations
from sqlalchemy.orm import Session
from backend.app.core.exceptions import EntityNotFoundError, NearMissError
from backend.app.core.logging import get_logger
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.pattern import NearMissPattern, Pattern
from backend.app.db.models.investigation import Investigation
from backend.app.services.agent.provider import get_provider
from backend.app.services.agent.safety import validate_safe_output
from backend.app.services.counterfactual.lab import InvalidSimulationError, simulate_near_miss
from backend.app.services.recommendations.recommendation_service import create_recommendation

log = get_logger("sandbox")
MAX_SCENARIOS = 5
PRESETS = [("START_RECOVERY_EARLIER", 10), ("REDUCE_RECOVERY_DURATION_PERCENT", 25),
           ("REDUCE_PEAK_PERCENT", 20)]


def _improvement(original: dict, simulated: dict) -> float:
    peak_gain = ((original["peak"] - simulated["peak"]) / original["peak"]
                 if original["peak"] else 0.0)
    od, sd = original["recovery_duration_seconds"], simulated["recovery_duration_seconds"]
    dur_gain = ((od - sd) / od if od else 0.0) if sd is not None and od else 0.0
    return round((peak_gain + dur_gain) / 2.0 * 100.0, 1)


def compare(db: Session, near_miss_id: str, scenarios: list[dict]) -> dict:
    nm = db.get(NearMiss, near_miss_id)
    if not nm:
        raise EntityNotFoundError(f"near-miss {near_miss_id} not found")
    if not isinstance(scenarios, list) or not scenarios or len(scenarios) > MAX_SCENARIOS:
        raise InvalidSimulationError(f"provide 1..{MAX_SCENARIOS} scenarios")
    options = []
    for spec in scenarios:
        if not isinstance(spec, dict) or "scenario" not in spec or "value" not in spec:
            raise InvalidSimulationError("each scenario needs {scenario, value}")
        sim = simulate_near_miss(db, near_miss_id, spec["scenario"], spec["value"])
        if sim["status"] != "SIMULATED":
            options.append({"scenario": spec["scenario"], "parameter": sim.get("parameter"),
                            "status": sim["status"], "improvement": None})
            continue
        imp = _improvement(sim["original"], sim["simulated"])
        options.append({"scenario": spec["scenario"], "parameter": sim["parameter"],
                        "status": "SIMULATED",
                        "original_peak": sim["original"]["peak"],
                        "simulated_peak": sim["simulated"]["peak"],
                        "original_recovery_seconds": sim["original"]["recovery_duration_seconds"],
                        "simulated_recovery_seconds": sim["simulated"]["recovery_duration_seconds"],
                        "improvement": imp})
    ranked = sorted([o for o in options if o["improvement"] is not None],
                    key=lambda o: (-o["improvement"], o["scenario"]))
    order = [options.index(o) for o in ranked]
    best = ranked[0] if ranked else None
    log.info(f"sandbox_compared nm={near_miss_id} best={best['scenario'] if best else None}")
    return {"mode": "COUNTERFACTUAL", "near_miss_id": near_miss_id, "options": options,
            "ranking": order,
            "best": best,
            "note": "Under the observed-data simulation, the top-ranked scenario produces "
                    "the largest modeled improvement. Not a real-world guarantee."}


def recommend_best(db: Session, near_miss_id: str, scenario: str, value) -> dict:
    sim = simulate_near_miss(db, near_miss_id, scenario, value)
    if sim["status"] != "SIMULATED":
        raise InvalidSimulationError(f"scenario not simulable: {sim['status']}")
    links = db.query(NearMissPattern).filter_by(near_miss_id=near_miss_id).all()
    inv = None
    for ln in links:
        inv = (db.query(Investigation).filter_by(pattern_id=ln.pattern_id)
               .order_by(Investigation.created_at.desc()).first())
        if inv:
            break
    if not inv:
        raise InvalidSimulationError("no investigation exists for this near-miss")
    imp = _improvement(sim["original"], sim["simulated"])
    rec = create_recommendation(
        db, inv.id,
        title=f"Modeled intervention: {scenario} ({value})",
        description=(f"Counterfactual replay of near-miss {near_miss_id[:8]} under {scenario} "
                     f"produced a modeled improvement of {imp}%."),
        expected_effect="If such an operational change were achievable, recurrence may warrant review.",
        confidence=0.6, recommendation_type="MODELED_INTERVENTION")
    return {"recommendation_id": rec.id, "investigation_id": inv.id,
            "improvement": imp, "execution": "PENDING_EXTERNAL_ACTION via intervention handoff"}


def explain_ranking(db: Session, result: dict) -> dict:
    from backend.app.services.chains.chain_detector import evidence_for_nm
    eids = evidence_for_nm(db, result["near_miss_id"])
    evs = [{"id": i, "type": "EVIDENCE", "description": "supporting evidence record"} for i in eids]
    bundle = {"ranking": result.get("ranking"), "best": result.get("best"),
              "options": result.get("options"), "evidence": evs}
    raw = get_provider().generate(bundle)
    raw["claims"] = [c for c in raw.get("claims", [])
                     if c.get("type") in ("FACT", "INFERENCE", "HYPOTHESIS", "SIMULATION")]
    return validate_safe_output(raw, set(eids))
