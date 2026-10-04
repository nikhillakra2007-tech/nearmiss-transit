"""Baseline engine: robust median per (route, time-bucket) + rolling average.
Methodology: group historical delays by (route_id, hour-bucket); baseline =
median; spread = MAD*1.4826; deviation if |delay − median| > sigma*spread and
delay > NEAR_MISS_THRESHOLD floor. Documented in docs/architecture + ADR-003.
"""
from __future__ import annotations
import statistics


def median_baseline(delays: list[float]) -> dict:
    if not delays:
        return {"median": 0.0, "mad": 0.0, "spread": 60.0, "n": 0}
    med = statistics.median(delays)
    mad = statistics.median([abs(d - med) for d in delays])
    spread = max(mad * 1.4826, 30.0)
    return {"median": float(med), "mad": float(mad), "spread": float(spread), "n": len(delays)}


def rolling_average(delays: list[float], window: int = 5) -> float:
    if not delays:
        return 0.0
    tail = delays[-window:]
    return sum(tail) / len(tail)


def is_deviation(delay: float, baseline: dict, sigma: float = 3.0, floor: float = 600.0) -> bool:
    if delay < floor:
        return False
    return abs(delay - baseline["median"]) > sigma * baseline["spread"]
