"""Recurrence grouping key: (route, hour-bucket, type). Deterministic, no LLM."""
from __future__ import annotations


def recurrence_key(near_miss) -> str:
    dt = near_miss.detected_at
    hour = dt.hour if dt else 0
    bucket = f"{hour:02d}:00-{(hour + 1) % 24:02d}:00"
    return f"{near_miss.route_id or 'noroute'}|{bucket}|{near_miss.near_miss_type}"
