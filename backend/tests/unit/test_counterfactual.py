"""Counterfactual lab tests (§21 plan, compact)."""
import pytest
from backend.app.services.counterfactual.lab import InvalidSimulationError, simulate

SERIES = [{"timestamp": f"2026-01-01T08:{m:02d}:00", "delay_minutes": d}
          for m, d in zip((0, 5, 10, 15, 20, 25, 30), (3, 7, 12, 16, 13, 9, 6))]


def test_valid_peak_reduction():
    out = simulate(SERIES, "REDUCE_PEAK_PERCENT", 25)
    assert out["status"] == "SIMULATED" and out["mode"] == "COUNTERFACTUAL"
    assert out["simulated"]["series"][3]["delay_minutes"] == 12  # peak point scaled
    assert out["delta"]["peak_minutes"] == -3  # residual max 13 vs original 16
    assert len(out["simulated"]["series"]) == len(SERIES)
    assert [p["timestamp"] for p in out["simulated"]["series"]] == [p["timestamp"] for p in SERIES]


def test_valid_recovery_shift_and_duration():
    a = simulate(SERIES, "START_RECOVERY_EARLIER", 3)
    assert a["status"] == "SIMULATED" and a["delta"]["recovery_seconds"] < 0
    b = simulate(SERIES, "REDUCE_RECOVERY_DURATION_PERCENT", 50)
    assert b["status"] == "SIMULATED" and b["delta"]["recovery_seconds"] < 0
    assert b["simulated"]["peak"] == 16  # peak untouched


def test_boundaries_1_and_50():
    assert simulate(SERIES, "REDUCE_PEAK_PERCENT", 1)["status"] == "SIMULATED"
    assert simulate(SERIES, "REDUCE_PEAK_PERCENT", 50)["simulated"]["series"][3]["delay_minutes"] == 8.0
    assert simulate(SERIES, "START_RECOVERY_EARLIER", 30)["status"] in ("SIMULATED", "INSUFFICIENT_SIMULATION_RESOLUTION")


@pytest.mark.parametrize("bad", [0, -5, 51, 999, "25", None, float("nan"), float("inf"), True])
def test_invalid_values_rejected(bad):
    with pytest.raises(InvalidSimulationError):
        simulate(SERIES, "REDUCE_PEAK_PERCENT", bad)


def test_invalid_scenario_and_short_series():
    with pytest.raises(InvalidSimulationError):
        simulate(SERIES, "DELETE_DELAYS", 10)
    out = simulate(SERIES[:2], "REDUCE_PEAK_PERCENT", 10)
    assert out["status"] == "INSUFFICIENT_DATA"


def test_insufficient_resolution_and_determinism():
    flat = [{"timestamp": f"2026-01-01T08:{m:02d}:00", "delay_minutes": 5} for m in (0, 5, 10)]
    out = simulate(flat, "START_RECOVERY_EARLIER", 30)
    assert out["status"] in ("SIMULATED", "INSUFFICIENT_SIMULATION_RESOLUTION")
    a = simulate(SERIES, "REDUCE_PEAK_PERCENT", 25)
    b = simulate(SERIES, "REDUCE_PEAK_PERCENT", 25)
    assert a == b and SERIES[3]["delay_minutes"] == 16  # original untouched
