# Clarifications/assumptions
- Backend report CLAIMED 22/22 → independently re-run (Stage 0). Result: 22/22 PASS confirmed.
- Postgres: pg_ctl 18.6 present → validate real migration (Stage 1 target GREEN).
- Feed: MBTA cdn.mbta.com keyless protobuf (VehiclePositions/TripUpdates/Alerts) → inspect first; fallback: other keyless feed; last resort: labelled replay.
- Frontend: static dependency-free app served by FastAPI (ADR-006) instead of Next.js — zero build, judging-friendly; same /api/v1 contract so Next.js can replace later.
- LLM: MockProvider default; real provider optional via env; agent-hardening via adversarial tests.
- Interventions stay PROPOSED/PENDING_EXTERNAL_ACTION (no fake execution).
- Ruff/mypy not installed → compileall + pytest are the gates; documented.
