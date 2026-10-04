# Final known limitations
- Postgres sandbox-unstable → Stage 1 YELLOW; managed PG for prod.
- Live MBTA snapshot all-on-time → near-miss shown on labelled replay (honest).
- Mock LLM default; real provider via env, unverified against paid API.
- No in-app rate limit; map deferred; ruff/mypy not run (unavailable).
- V2.6 replay is historical validation only (observed data ≤ cutoff, capped
  180-min lookback); demo fixture enters the window already EMERGING, so the
  demo shows "EMERGING 60 min before" rather than a NORMAL→WATCH→EMERGING
  crossing. No future-prediction claim is made.
