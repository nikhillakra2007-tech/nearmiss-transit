"""Correlation: near-misses sharing route + overlapping stop/time signatures."""
from __future__ import annotations


def correlate(a: dict, b: dict) -> float:
    score = 0.0
    if a.get("route_id") and a["route_id"] == b.get("route_id"):
        score += 0.5
    if a.get("hour_bucket") == b.get("hour_bucket"):
        score += 0.3
    if a.get("type") == b.get("type"):
        score += 0.2
    return round(score, 2)
