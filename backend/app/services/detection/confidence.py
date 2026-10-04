"""Confidence scoring: evidence strength → 0..1 (deterministic)."""
from __future__ import annotations


def confidence(n_points: int = 0, peak: float = 0.0, threshold: float = 600.0, has_alert: bool = False) -> float:
    score = 0.4
    score += min(n_points * 0.05, 0.25)
    if peak >= threshold * 1.5:
        score += 0.15
    elif peak >= threshold:
        score += 0.08
    if has_alert:
        score += 0.1
    return round(max(0.0, min(score, 0.95)), 3)
