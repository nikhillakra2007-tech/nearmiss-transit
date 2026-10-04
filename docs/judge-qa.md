# Judge Q&A (answers match implementation)
1. Novel? Detects recovered operational near-misses + recurring multi-route
   temporal sequences + deterministic forecast/simulation/verification loop.
2. Not a chatbot? Detection, scores, chains, sims are deterministic code;
   the LLM only explains validated evidence (MockProvider default).
3. Data? GTFS-Realtime (MBTA keyless feeds) + labelled REPLAY fixtures.
4. Real? Live feed parsed genuinely (932 events observed); demo story uses
   REPLAY because live snapshots were all-on-time (zero delays, zero
   near-misses — honestly reported).
5. Why replay? Guarantees the deterministic 42→17→8 + EMERGING story without
   depending on live service levels; always badged REPLAY.
6. Hallucinations? Evidence-ID validation rejects unknown IDs; claims typed.
7. False causality? Whole-word ban list (caused/cause/causal/proof/…);
   vocabulary fixed to MAY_CONTRIBUTE_TO / temporal association.
8. Forecast how? Six weighted heuristics over observed data ≤ evaluated_at;
   bands 30/60; <3 signals → INSUFFICIENT_DATA.
9. ML? No. Configured constants, documented, reproducible.
10. Counterfactuals? Deterministic transforms of observed series; ephemeral.
11. Predictions? No — bannered HYPOTHETICAL SIMULATION.
12. Chains? Ordered start-time pairs within 120 min, same-vehicle excluded,
    grouped by route signature, strength by recurrence count.
13. Operational use? Prioritize corridors (resilience), review schedules,
    prepare handoffs, verify outcomes.
14. Insufficient data? Explicit INSUFFICIENT_DATA states everywhere; never 0/100.
15. Feed down? Typed FEED_UNAVAILABLE; replay unaffected.
16. Next? Managed-Postgres deploy, real agency handoff API, live cascade
    observation over longer windows.
17. How do you know your forecast is useful? NearMiss Transit can replay
    historical events using only observations available at each earlier
    cutoff, showing when its deterministic forecast would have entered
    WATCH or EMERGING before a recorded near-miss
    (`GET /api/v1/patterns/{id}/early-warning`, mode HISTORICAL_REPLAY).
    This is historical validation, not a claim of future prediction
    accuracy.
