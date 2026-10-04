# NearMiss Transit — Backend Spec (SPECIFY)

## WHAT
Backend + database foundation for an operational near-miss agent over live
GTFS-Realtime data. Pipeline: INGEST → NORMALIZE → STORE → STATE →
DETECT → CORRELATE → INVESTIGATE → RECOMMEND → INTERVENE → VERIFY.

## WHY
Transit agencies see repeated "almost-failures" (severe delay spikes that
recover before cancellation, temporary deviations, alert-then-recovery).
A persistent memory + deterministic detection + evidence-grounded agent
turns one-off monitoring into a learning loop.

## CONSTRAINTS
- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL.
- Modular monolith; no Redis/Kafka/Celery/microservices/vector DB.
- Deterministic detection; LLM optional and replaceable.
- Idempotent workers; retention-bounded raw storage.
- No frontend in this phase.

## SUCCESS CRITERIA
See specs/nearmiss-backend/verification.md (20 backend checks: migrations,
fetch→parse→store, dedupe, state, delay, near-miss, pattern, investigation,
evidence-grounded agent, recommendation, intervention, verification, API,
tests, docs).

## NON-GOALS
Frontend, mobile, chatbot, ticketing, fares, route planner, accident/safety
prediction, surveillance, profiling, autonomous external actions, fake
municipal integrations, unnecessary ML/microservices.

## RISKS
- Feed heterogeneity (missing fields) → defensive parsing + per-entity errors.
- High-frequency positions → retention/aggregation config + indexes.
- Hallucinated agent claims → evidence-ID validation, structured output schema.
- Postgres unavailable in CI/judging → SQLite-compatible types + DEMO/REPLAY mode.

## ARCHITECTURE
`backend/app`: core / db(models) / schemas / repositories / services
(ingestion, transit, detection, patterns, investigation, agent,
recommendations, interventions, verification) / api(v1 routes) / workers.
See plan.md + docs/architecture/*.

## DATA MODEL
15 entities: agency, route, stop, trip, vehicle, transit_event, service_alert,
near_miss, near_miss_pattern, pattern, investigation, evidence, causal_edge,
recommendation, intervention, verification. See data-model.md.

## API CONTRACT
Versioned `/api/v1` (health, agencies, routes, stops, vehicles, events,
near-misses, patterns, investigations, recommendations, interventions,
verifications, ingestion/run). See api-contract.md.

## AGENT CONTRACT
Evidence-grounded JSON: summary + typed claims (FACT/INFERENCE/HYPOTHESIS
with evidence_ids + confidence) + recommendation. Unknown IDs rejected.
See agent-contract.md.

## TEST STRATEGY
Unit (delay, baseline, deviation, recovery, recurrence, confidence, evidence,
agent validation) + integration (migrations, repos, ingestion, API, pipelines)
+ GTFS fixtures (valid/malformed/missing/duplicate/stale/alert) + mocked-LLM
agent tests. SQLite for tests, Postgres for prod.
