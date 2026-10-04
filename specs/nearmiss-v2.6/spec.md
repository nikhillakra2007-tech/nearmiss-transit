# V2.6 Early-Warning Replay — spec

Problem: operators see the current forecast score but cannot tell whether the
signal would have appeared early enough to matter before a recorded
near-miss. Goal: replay historical observations through the EXISTING
deterministic forecast engine at earlier cutoffs and report when the
forecast entered WATCH / EMERGING before the event.

Non-goals: new scoring, ML, prediction claims, external services, new
tables, browser automation, forecast-logic changes.

## Contract

`GET /api/v1/patterns/{pattern_id}/early-warning`
query: `at` (ISO, optional history bound), `lookback_minutes` (default 60,
1..180), `step_minutes` (default 15, >= 5). Out-of-range → typed 422.
Unknown pattern → 404 via existing conventions.

Response (`mode` always `HISTORICAL_REPLAY`):

- `target_near_miss_id`, `target_timestamp` (latest member start <= `at`)
- `lookback_minutes`, `step_minutes`, `timeline`, `first_watch`,
  `first_emerging`, `available_history`, `disclaimer`, `status`
  (`COMPLETE` | `INSUFFICIENT_DATA`)
- timeline point: `cutoff`, `minutes_before_target`, `score|null`,
  `band` (forecast status verbatim), `signals_available`,
  `signals` (name/available/value/contribution/summary only)
- `first_watch`: first point with band in (WATCH, EMERGING);
  `first_emerging`: first point with band EMERGING; else null (never zero)
- zero members in scope → `INSUFFICIENT_DATA`, empty timeline, honest reason
- per-point INSUFFICIENT_DATA keeps `score: null`, never 0, never NORMAL

## Correctness rules

1. No leakage: every cutoff evaluates `forecast_pattern(db, id, at=cutoff)`,
   which filters all inputs to `observed_at <= cutoff` by construction.
   No bulk preloading of future series into scoring helpers.
2. No duplication: weights, bands, redistribution stay inside
   `forecast.engine`; replay reads bands from result `status` only.
3. Deterministic: same DB + params → identical JSON (replay is pure read).
4. Safe language only: historical replay / emerging stress / earlier warning
   / observed pattern / deterministic forecast score / historical cutoff /
   evidence-supported signal. Banned: will fail, guarantee(d), unsafe,
   dangerous, accident, cause/caused by, prediction certainty,
   predicted failure. Never "predicted the disruption"; instead
   "Historical replay shows the forecast entered WATCH X minutes before
   the recorded near-miss."

## Frontend

Replay section inside pattern detail: `EARLY-WARNING REPLAY` heading,
`HISTORICAL REPLAY` badge (never LIVE/PREDICTION wording), summary line
("First WATCH: N minutes before near-miss" only when found), vertical
timeline list + target marker, full `<table>` text alternative, per-point
`<select>` signal breakdown (score/band/cutoff/minutes/signals),
keyboard/focus/aria + reduced-motion + overflow conventions preserved.

## Demo

Reuse REPLAY fixtures. Probe route-42 pattern replay first; smallest
deterministic fixture tweak only if the timeline shows no transition.
Story: DETECT → REMEMBER → CONNECT → FORECAST → EARLY-WARNING REPLAY →
SIMULATE → RECOMMEND → VERIFY.

## Tests (mandatory)

Endpoint happy path, mode field, first WATCH, first EMERGING, null when
never crossed, insufficient history, invalid lookback, invalid step,
lookback cap, no-leakage regression (future insert cannot move earlier
cutoff), determinism, forecast unchanged, typed errors, safety sweep,
frontend served, badge present, table present. Full suite must stay green.
