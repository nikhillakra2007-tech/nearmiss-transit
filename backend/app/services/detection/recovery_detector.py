"""Recovery detector: escalation → peak → recovery → normal.
Input: ordered [(timestamp, delay)] series. Returns peak/start/recovery stats.
"""
from __future__ import annotations
from datetime import datetime


def detect_recovery(series: list[tuple], abnormal_floor: float = 600.0, recovery_ceiling: float = 300.0) -> dict | None:
    if len(series) < 3:
        return None
    delays = [d for _, d in series if d is not None]
    if not delays:
        return None
    peak_idx = max(range(len(delays)), key=lambda i: delays[i])
    peak = delays[peak_idx]
    if peak < abnormal_floor:
        return None
    # must have escalation before peak and recovery after peak
    if peak_idx == 0 or peak_idx == len(delays) - 1:
        return None
    if not (delays[peak_idx] > delays[0]):
        return None
    final = delays[-1]
    if final > recovery_ceiling:
        return None
    start_t, peak_t, rec_t = series[0][0], series[peak_idx][0], series[-1][0]

    def _secs(a, b) -> int | None:
        try:
            return int((b - a).total_seconds())
        except Exception:
            return None
    return {"peak": peak, "start_time": start_t, "peak_time": peak_t, "recovery_time": rec_t,
            "recovery_duration_seconds": _secs(start_t, rec_t), "final": final}
