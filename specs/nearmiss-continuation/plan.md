# Continuation plan (stage-gated)
0 audit (done: 22/22, node24, pg18 present) → 1 Postgres clean-migrate + constraint checks →
2 fetch+parse MBTA feed, docs/gtfs/selected-feed.md → 3 persist real rows, idempotency/stale/malformed →
4 run detector on real data; replay fallback labelled → 5 full chain to recommendation →
6 adversarial agent tests (hallucination/injection/unavailable) → 7 intervention/verification windows →
8 frontend spec → 9 static frontend slices → 10 integration (LIVE/REPLAY badge, error/empty states) →
11 e2e validation doc → 12 UX/a11y pass → 13 security audit → 14 deploy docs → 15 smoke →
16 demo script → 17 final audit → 18 docs/handoff. Gate rule: RED stops the line.
