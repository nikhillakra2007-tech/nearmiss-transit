from datetime import datetime, timezone, timedelta
from backend.app.services.transit.delay_engine import compute_delay_seconds
from backend.app.services.transit.baseline import median_baseline, is_deviation
from backend.app.services.detection.recovery_detector import detect_recovery
from backend.app.services.detection.confidence import confidence
from backend.app.services.agent.planner import validate_agent_output
from backend.app.core.exceptions import AgentOutputRejectedError
import pytest


def test_delay_zero():
    t = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    assert compute_delay_seconds(t, t) == 0


def test_delay_positive_negative():
    t = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    assert compute_delay_seconds(t + timedelta(seconds=300), t) == 300
    assert compute_delay_seconds(t - timedelta(seconds=120), t) == -120


def test_delay_missing():
    t = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
    assert compute_delay_seconds(None, t) is None
    assert compute_delay_seconds(t, None) is None


def test_delay_tz():
    import pytz
    eastern = pytz.timezone("US/Eastern")
    o = eastern.localize(datetime(2026, 1, 1, 8, 5))
    s = eastern.localize(datetime(2026, 1, 1, 8, 0))
    assert compute_delay_seconds(o, s) == 300


def test_baseline_median():
    b = median_baseline([60, 90, 120, 90, 100])
    assert b["median"] == 90
    assert not is_deviation(100, b)
    assert is_deviation(1200, b)


def test_recovery_detected():
    now = datetime.now(timezone.utc)
    series = [(now + timedelta(minutes=i), d) for i, d in enumerate([300, 540, 900, 1080, 960, 600, 360, 240])]
    rec = detect_recovery(series)
    assert rec is not None and rec["peak"] == 1080


def test_recovery_no_peak_returns_none():
    now = datetime.now(timezone.utc)
    series = [(now + timedelta(minutes=i), d) for i, d in enumerate([60, 90, 120, 100])]
    assert detect_recovery(series) is None


def test_confidence_range():
    assert 0.0 <= confidence(8, 1200) <= 1.0


def test_agent_output_validation_accepts_and_rejects():
    good = {"summary": "s", "claims": [{"type": "FACT", "statement": "x", "evidence_ids": ["e1"], "confidence": 0.9}],
            "possible_causes": [], "recommendation": {"title": "t", "description": "d"}}
    assert validate_agent_output(good, {"e1"})["summary"] == "s"
    bad = {"summary": "s", "claims": [{"type": "FACT", "statement": "x", "evidence_ids": ["ghost"], "confidence": 0.9}],
           "possible_causes": [], "recommendation": {"title": "t", "description": "d"}}
    with pytest.raises(AgentOutputRejectedError):
        validate_agent_output(bad, {"e1"})
