"""Threshold engine: significance gate for candidate deviations."""
from __future__ import annotations


def is_significant(delay: float, threshold: float = 600.0, min_escalation: float = 180.0, peak: float | None = None) -> bool:
    if delay < threshold:
        return False
    if peak is not None and (peak - delay) < 0 and (threshold - delay) > 0:
        return False
    return True
