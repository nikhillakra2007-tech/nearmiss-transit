# Plan (PLAN) — NearMiss Transit backend

## Slices
01 foundation: config/logging/FastAPI/health/DB session (sqlite+postgres).
02 database: UUID PKs, external IDs, JSONB-variant, indexes, FKs (no cascade
   on history), Alembic initial migration.
03 transit entities: agencies/routes/stops/trips/vehicles + schemas/repos.
04 GTFS ingestion: httpx client (timeout/retry/backoff), protobuf parser,
   normalizer → NormalizedTransitEvent, idempotent persist (source_event_id).
05 state engine: delay = observed − scheduled; baselines (median per
   route/stop/time-bucket + rolling avg); state reconstruction with
   OBSERVED/DERIVED/INFERENCE/COUNTERFACTUAL separation.
06 near-miss detector: deviation × escalation × recovery × significance;
   recovery detector (peak/start/peak-time/recovery/duration).
07 patterns: deterministic recurrence grouping (route/stop-cluster/time
   window/dow/signature), pattern persistence, idempotent.
08 investigation: evidence bundle (WHAT/WHEN/WHERE/HOW OFTEN/HOW SEVERE/
   vs-normal/EVIDENCE), lifecycle.
09 agent: provider abstraction (mock + env-configured), tools boundary,
   structured-output validation, evidence-ID enforcement.
10 recommendations/interventions: grounded recs; InterventionExecutor
   abstraction (PROPOSED/PENDING_EXTERNAL_ACTION, never fake execution).
11 verification: before/after metrics → IMPROVED/NO_SIGNIFICANT_CHANGE/
   WORSENED/INSUFFICIENT_DATA.
12 API: all /api/v1 routes + pagination/filtering/errors.
13 pipeline: LIVE→…→VERIFY wired through workers (lightweight asyncio loops).
14 hardening: tests/indexes/logging/docs/security.

## Decisions
- Sync SQLAlchemy 2.x (reliable under hackathon) with postgres JSONB-variant
  so SQLite tests run; async workers via asyncio.to_thread where needed.
- `gtfs-realtime-bindings` for protobuf; dict-fixture path for tests/demo.
- Mock LLM default; real provider via env without code change.
