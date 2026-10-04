# Operational domino (chain detection)
Concept: recurring ordered near-miss pairs (A starts before B within
CHAIN_WINDOW_MINUTES=120), grouped by (routeA, typeA, routeB, typeB).
Ordering uses start-event observed_at. Strength: OBSERVED_ONCE (1),
RECURRING (2–3), STRONG_RECURRING (≥4) — relationship strength, never causal
confidence. This is NOT causal inference: vocabulary is MAY_CONTRIBUTE_TO /
TEMPORALLY ASSOCIATED_WITH / RECURRING SEQUENCE; every chain view carries
"Temporal association, not causal proof." Architecture: stateless computed
service (services/chains) — no new tables because causal_edges is
investigation-scoped; plus one membership-link fix in pattern_detector
(late members now linked). Evidence: reuses pattern-investigation Evidence
rows; agent output validated for evidence membership AND causal-certainty
language (whole-word ban; "unproven" hedges pass). Investigate endpoint is
ephemeral (returned, not persisted). Verification: chains accept since/until
so before/after occurrence counts compare deterministically; outcomes stay
backend-authoritative (no frontend inference). Demo: REPLAY Route 42 → Route 17
lagged windows (4×, ~12 min gap) via scripts/seed_demo.py (idempotent).
Limits: window/thresholds configured not learned; same-vehicle pairs excluded;
unverified against live multi-route cascades.
V2.1 live validation (2026-10-04): fresh MBTA snapshot — 932 events, 106
routes, 205 vehicles, but all 481 delay readings 0s → 0 near-misses, 0 chains.
NO LIVE CASCADE OBSERVED (honest result; algorithm untouched). Live pipeline
technically supports chains (ingest→detect→chains ran clean). Replay demo:
DATABASE_URL=sqlite:///./demo.db python scripts/prep_demo.py, then serve with
DEMO_MODE=true for honest REPLAY labelling.
V2.3 multi-hop: services/chains/multihop.py builds edge-to-edge trails
(≤CHAIN_MAX_DEPTH=3) from pairwise occurrences; rejects repeated nodes/routes;
groups by route sequence; evidence-less sequences excluded; GET
patterns/{id}/multihop. Demo: 42→17→8 STRONG_RECURRING ×4 (gaps 12.0/12.0).
