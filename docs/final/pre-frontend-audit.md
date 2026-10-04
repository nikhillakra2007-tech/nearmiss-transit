# Pre-frontend audit (independent re-verification, 2026-10-04)
Architecture: modular monolith backend/app + static frozen frontend/ (untouched
this phase — verified: no writes under frontend/; contract reads only).
Capabilities (all re-proven): GTFS fetch/parse/persist/idempotent (MBTA live
477 entities today; 418-row persist earlier); detector (abnormal+deviation+
escalation+recovery; cancellations excluded; pre-escalation baseline);
deterministic (route,hour,type) patterns, idempotent; evidence-typed agent
with adversarial rejection; PENDING_EXTERNAL_ACTION honesty; 4 verification
outcomes (IMPROVED/WORSENED now directly tested).
Verification evidence: 44/44 pytest; contract probe (404/422/CORS/empty-mode);
migration --sql 17 tables; retry-exhaustion typed error; empty-evidence chain
safe; clean-DB demo reproduced (3 near-misses → 1 pattern → handoff).
No stale claims: grep finds no TODOs, no fake-live language, no EXECUTED claims.
Known limitations: sandbox PG ENVIRONMENT_BLOCKED (app-side VERIFIED);
live snapshot all-zero delays → REPLAY labelled; Mock LLM default;
no in-app rate limit (proxy concern); ruff/mypy unavailable.
Remaining before frontend: none on backend — FROZEN. Frontend is next phase.
