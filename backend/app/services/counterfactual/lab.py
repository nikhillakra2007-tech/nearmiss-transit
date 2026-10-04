"""Counterfactual Lab — deterministic hypothetical replays of observed series.

Allow-listed scenarios only; no formulas, no code execution, no invented
points. Statuses: SIMULATED | INSUFFICIENT_DATA | INSUFFICIENT_SIMULATION_RESOLUTION.
"""
from __future__ import annotations
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.core.exceptions import InvalidTransitEventError, NearMissError
from backend.app.db.models.near_miss import NearMiss
from backend.app.db.models.transit_event import TransitEvent
from backend.app.services.transit.series import delay_series_for

SCENARIOS = ("REDUCE_PEAK_PERCENT", "START_RECOVERY_EARLIER", "REDUCE_RECOVERY_DURATION_PERCENT")


class InvalidSimulationError(NearMissError):
    code = "INVALID_SIMULATION"
    status_code = 422


def _num(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidSimulationError("parameter must be numeric")
    if not math.isfinite(value):
        raise InvalidSimulationError("parameter must be finite")
    return float(value)


def _validate(scenario: str, value) -> float:
    if scenario not in SCENARIOS:
        raise InvalidSimulationError(f"unsupported scenario: {scenario}")
    v = _num(value)
    if scenario == "START_RECOVERY_EARLIER":
        if not (1 <= v <= 30):
            raise InvalidSimulationError("minutes must be within 1..30")
    else:
        if not (1 <= v <= 50):
            raise InvalidSimulationError("percentage must be within 1..50")
    return v


def _metrics(series: list[dict]) -> dict:
    vals = [p["delay_minutes"] for p in series]
    dur = None
    try:
        t0 = datetime.fromisoformat(series[0]["timestamp"])
        t1 = datetime.fromisoformat(series[-1]["timestamp"])
        dur = int((t1 - t0).total_seconds())
    except Exception:
        dur = None
    return {"peak": max(vals), "final": vals[-1], "recovery_duration_seconds": dur}


def _peak_index(series: list[dict]) -> int:
    return max(range(len(series)), key=lambda i: series[i]["delay_minutes"])


def simulate(series: list[dict], scenario: str, value) -> dict:
    v = _validate(scenario, value)
    if len(series) < 3:
        return {"mode": "COUNTERFACTUAL", "scenario": scenario, "parameter": v,
                "original": None, "simulated": None,
                "delta": None, "status": "INSUFFICIENT_DATA"}
    original = {"series": [dict(p) for p in series], **_metrics(series)}
    peak = original["peak"]
    pi = _peak_index(series)
    sim = [dict(p) for p in series]
    if scenario == "REDUCE_PEAK_PERCENT":
        new_peak = round(peak * (1 - v / 100.0), 1)
        for p in sim:
            if p["delay_minutes"] == peak:
                p["delay_minutes"] = new_peak
    elif scenario == "START_RECOVERY_EARLIER":
        post = sim[pi + 1:]
        if not post:
            return _insufficient(scenario, v, original)
        shifted = []
        for p in post:
            try:
                t = datetime.fromisoformat(p["timestamp"]) - timedelta(minutes=v)
            except Exception:
                return _insufficient(scenario, v, original)
            shifted.append({**p, "timestamp": t.isoformat()})
        try:
            peak_t = datetime.fromisoformat(sim[pi]["timestamp"])
            if any(datetime.fromisoformat(p["timestamp"]) <= peak_t for p in shifted):
                return _insufficient(scenario, v, original)
        except Exception:
            return _insufficient(scenario, v, original)
        sim = sim[:pi + 1] + shifted
    else:  # REDUCE_RECOVERY_DURATION_PERCENT
        post = sim[pi + 1:]
        if len(post) < 2:
            return _insufficient(scenario, v, original)
        try:
            peak_t = datetime.fromisoformat(sim[pi]["timestamp"])
            factor = 1 - v / 100.0
            new_post = []
            for p in post:
                t = datetime.fromisoformat(p["timestamp"])
                nt = peak_t + (t - peak_t) * factor
                new_post.append({**p, "timestamp": nt.isoformat()})
            sim = sim[:pi + 1] + new_post
        except Exception:
            return _insufficient(scenario, v, original)
    sm = {"series": sim, **_metrics(sim)}
    d_dur = None
    if original["recovery_duration_seconds"] is not None and sm["recovery_duration_seconds"] is not None:
        d_dur = sm["recovery_duration_seconds"] - original["recovery_duration_seconds"]
    return {"mode": "COUNTERFACTUAL", "scenario": scenario, "parameter": v,
            "original": original, "simulated": sm,
            "delta": {"peak_minutes": round(sm["peak"] - original["peak"], 1),
                      "recovery_seconds": d_dur},
            "status": "SIMULATED"}


def _insufficient(scenario: str, v: float, original: dict) -> dict:
    return {"mode": "COUNTERFACTUAL", "scenario": scenario, "parameter": v,
            "original": original, "simulated": None, "delta": None,
            "status": "INSUFFICIENT_SIMULATION_RESOLUTION"}


def simulate_near_miss(db: Session, near_miss_id: str, scenario: str, value) -> dict:
    nm = db.get(NearMiss, near_miss_id)
    if not nm:
        from backend.app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError(f"near-miss {near_miss_id} not found")
    start = db.get(TransitEvent, nm.start_event_id) if nm.start_event_id else None
    rec = db.get(TransitEvent, nm.recovery_event_id) if nm.recovery_event_id else None
    series = delay_series_for(db, nm, start, rec)
    return simulate(series, scenario, value)
