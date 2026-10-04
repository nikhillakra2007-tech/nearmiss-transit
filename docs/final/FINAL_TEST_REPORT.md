# Final test report — 39/39 passing
Unit: delay/baseline/recovery/confidence/agent-validation/adversarial (hallucination,
injection, outage). Integration: constraints, ingestion idempotency, GTFS fixtures
(valid/malformed/missing/duplicate/stale/alert), full pipeline, intervention honesty,
4-outcome verification, API, frontend+detail chain. Live-data: 42 MBTA vehicles,
0 false positives. Command: `python -m pytest backend/tests -q`.
