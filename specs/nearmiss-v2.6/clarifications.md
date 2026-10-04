# V2.6 internal clarifications (no user round-trip; resolved from codebase)

1. Target event: latest pattern member (by start-event `observed_at`,
   fallback `detected_at`) with start <= `at` (default now). Rationale:
   `_members_upto` in forecast engine already defines membership this way;
   reuse keeps target consistent with what the forecast itself can see.
2. Cutoff grid: `target-lookback … target` stepping `step_minutes`, always
   including `target` itself as the final point. Rationale: matches the
   T-60…T example; every point still uses only `observed_at <= cutoff`.
3. `at` semantics: upper history bound for member/target selection, not the
   anchor. Anchor is always the target near-miss start. Default: now.
4. INSUFFICIENT_DATA: HTTP 200 with `status: INSUFFICIENT_DATA` (mirrors
   existing forecast endpoint convention) — zero members → empty timeline;
   members present but <3 signals at every cutoff → timeline of null-score
   points. Never 0, never NORMAL for missing history.
5. Bands: read from forecast `status`, never re-implemented (30/60 stay in
   one place). `first_watch` = first WATCH-or-EMERGING point.
6. Signals per point: trimmed to name/available/value/contribution/summary;
   evidence ids omitted for payload size (top-level forecast already links
   evidence; detail endpoint traces it).
7. Route placement: `v22.py` router next to `get_forecast` (forecast family,
   no `main.py` change, no new router file).
8. Validation: FastAPI-typed ints (auto-422 on type errors) + explicit
   `HTTPException(422)` range checks, mirroring `_parse`/`max_depth`.
9. Frontend home: pattern detail view (`openPattern`), after chains and
   before the counterfactual lab — matches the demo story order.
10. Fixture tweak: only if the probed route-42 replay shows no WATCH→
    EMERGING movement; prefer zero fixture change.
