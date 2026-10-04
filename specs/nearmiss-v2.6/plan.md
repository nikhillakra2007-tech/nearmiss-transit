# V2.6 plan

1. Service `backend/app/services/forecast/replay.py` (new, ~150 lines):
   target resolution via member starts <= end; cutoff grid builder;
   per-cutoff `forecast_pattern` reuse; first WATCH/EMERGING derivation
   from `status`; trimmed signals; `available_history`; disclaimer.
   No new tables, no weight/band duplication, no future reads.
2. Endpoint in `backend/app/api/routes/v22.py`: typed params, 422 caps
   (lookback 1..180, step >= 5), 404 mapping via `NearMissError`.
3. Probe on scratch demo DB: seed + detect + patterns, call service over
   route-42 pattern, inspect timeline movement. Decide fixture tweak.
4. Frontend: replay section in `openPattern` (`app.js`), `HISTORICAL
   REPLAY` badge reuse (`.badge.replay`), `<ol>` timeline + `<table>`
   alternative + `<select>` breakdown; tiny CSS addition; no new deps.
5. Tests `backend/tests/integration/test_early_warning.py`: 17 mandatory
   cases incl. no-leakage regression + determinism + safety sweep +
   frontend-served/badge/table.
6. Docs: README pipeline + judge Q&A ("How do you know your forecast is
   useful?") + demo scripts + api-overview + architecture diagram note +
   features/early-warning-replay.md + docs/v2.6-validation.md +
   known-limitations entry. Perf measured and recorded.
7. Final: full suite, compileall, frontend syntax check (node or
   equivalent), contract probes, prep_demo ×2 idempotency, security sweep,
   safety sweep, perf note, V2.6 report.
