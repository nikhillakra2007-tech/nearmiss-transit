"""Deterministic delay: observed − scheduled (seconds). LLM never computes this."""
from __future__ import annotations
from datetime import datetime


def compute_delay_seconds(observed: datetime | None, scheduled: datetime | None) -> int | None:
    if observed is None or scheduled is None:
        return None
    o = observed if observed.tzinfo else observed.replace(tzinfo=None)
    s = scheduled if scheduled.tzinfo else scheduled.replace(tzinfo=None)
    # normalize: if one naive one aware, compare wall times (tests use consistent tz)
    try:
        return int((observed - scheduled).total_seconds())
    except Exception:
        return None
