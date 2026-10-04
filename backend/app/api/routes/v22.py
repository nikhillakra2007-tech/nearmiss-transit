"""V2.2 endpoints: counterfactual lab, fingerprints, resilience radar."""
from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.api.deps import get_db
from backend.app.core.exceptions import NearMissError
from backend.app.services.counterfactual.explain import explain_simulation
from backend.app.services.counterfactual.lab import simulate_near_miss
from backend.app.services.fingerprints.engine import fingerprint_for, similar_patterns
from backend.app.services.forecast.engine import forecast_pattern
from backend.app.services.forecast.explain import explain_forecast
from backend.app.services.forecast.replay import (
    DEFAULT_LOOKBACK_MINUTES,
    DEFAULT_STEP_MINUTES,
    MAX_LOOKBACK_MINUTES,
    MIN_STEP_MINUTES,
    replay_early_warning,
)
from backend.app.services.resilience.radar import overview
from backend.app.services.sandbox.compare import PRESETS, compare, explain_ranking, recommend_best

router = APIRouter()


def _parse(dt: str | None):
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt)
    except ValueError:
        raise HTTPException(422, f"bad datetime: {dt}")


class SimulateIn(BaseModel):
    scenario: str
    value: float | int | str | bool | None = None
    explain: bool = False


@router.post("/near-misses/{near_miss_id}/simulate")
def simulate(body: SimulateIn, near_miss_id: str, db: Session = Depends(get_db)):
    try:
        result = simulate_near_miss(db, near_miss_id, body.scenario, body.value)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)
    if body.explain and result.get("status") == "SIMULATED":
        try:
            result["agent"] = explain_simulation(db, near_miss_id, result)
        except NearMissError as e:
            raise HTTPException(e.status_code, e.code)
    return result


@router.get("/patterns/{pattern_id}/fingerprint")
def get_fingerprint(pattern_id: str, db: Session = Depends(get_db)):
    try:
        return fingerprint_for(db, pattern_id)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)


@router.get("/patterns/{pattern_id}/similar")
def get_similar(pattern_id: str, n: int = 5, db: Session = Depends(get_db)):
    try:
        return {"pattern_id": pattern_id, "similar": similar_patterns(db, pattern_id, n)}
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)


@router.get("/resilience")
def get_resilience(since: str | None = None, until: str | None = None,
                   route_id: str | None = None, limit: int = 50,
                   db: Session = Depends(get_db)):
    return {"items": overview(db, None, _parse(since), _parse(until), route_id,
                              min(max(limit, 1), 200)),
            "disclaimer": "Operational resilience indicator derived from observed "
                          "historical behavior. Not a safety or failure prediction."}


@router.get("/patterns/{pattern_id}/forecast")
def get_forecast(pattern_id: str, at: str | None = None, explain: bool = False,
                 db: Session = Depends(get_db)):
    try:
        result = forecast_pattern(db, pattern_id, _parse(at))
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)
    if explain and result.get("status") != "INSUFFICIENT_DATA":
        try:
            result["agent"] = explain_forecast(db, result)
        except NearMissError as e:
            raise HTTPException(e.status_code, e.code)
    return result


@router.get("/patterns/{pattern_id}/early-warning")
def get_early_warning(pattern_id: str, at: str | None = None,
                      lookback_minutes: int = DEFAULT_LOOKBACK_MINUTES,
                      step_minutes: int = DEFAULT_STEP_MINUTES,
                      db: Session = Depends(get_db)):
    """Historical replay: existing forecast re-evaluated at earlier cutoffs.

    Caps: lookback_minutes within 1..180, step_minutes >= 5. Out-of-range
    values are rejected with typed 422 responses.
    """
    if not (1 <= lookback_minutes <= MAX_LOOKBACK_MINUTES):
        raise HTTPException(422, f"lookback_minutes must be within 1..{MAX_LOOKBACK_MINUTES}")
    if step_minutes < MIN_STEP_MINUTES:
        raise HTTPException(422, f"step_minutes must be >= {MIN_STEP_MINUTES}")
    try:
        return replay_early_warning(db, pattern_id, _parse(at),
                                    lookback_minutes, step_minutes)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)


class SandboxIn(BaseModel):
    scenarios: list[dict] | None = None
    explain: bool = False


class SandboxRecommendIn(BaseModel):
    scenario: str
    value: float | int | str | bool | None = None


@router.post("/near-misses/{near_miss_id}/sandbox")
def run_sandbox(near_miss_id: str, body: SandboxIn, db: Session = Depends(get_db)):
    try:
        specs = body.scenarios if body.scenarios is not None else [
            {"scenario": s, "value": v} for s, v in PRESETS]
        result = compare(db, near_miss_id, specs)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)
    if body.explain and result.get("best"):
        try:
            result["agent"] = explain_ranking(db, result)
        except NearMissError as e:
            raise HTTPException(e.status_code, e.code)
    return result


@router.post("/near-misses/{near_miss_id}/sandbox/recommend")
def sandbox_recommend(near_miss_id: str, body: SandboxRecommendIn,
                      db: Session = Depends(get_db)):
    try:
        return recommend_best(db, near_miss_id, body.scenario, body.value)
    except NearMissError as e:
        raise HTTPException(e.status_code, e.code)
