# Project Constitution — NearMiss Transit

## Product thesis
Persistent operational agent observing live transit, detecting recurring
operational near-misses (deviation → escalation → recovery, no full failure),
investigating recurrence, recommending interventions, verifying outcomes.

## Non-negotiables
1. Deterministic system owns facts/metrics/detection/evidence. LLM never
   computes deterministic facts (delays, baselines, recurrence).
2. Never fabricate agencies, routes, vehicles, trips, stops, delays,
   timestamps, alerts, or detections. Demo data is labelled DEMO/REPLAY.
3. Operational near-misses only — never claim safety incidents, danger, or
   accidents unless data supports it.
4. System works with LLM unavailable (mock provider fallback).
5. All agent claims traceable to stored evidence IDs; hallucinated IDs rejected.
6. Secrets via env vars only. LLM output is untrusted input — never executed.
7. Modular monolith. Domain logic independent of routes; models independent
   of schemas; ingestion independent of detection; detection independent of LLM.
8. Every slice independently verifiable with tests.
