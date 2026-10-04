# Domino (operational chain) detection — spec
WHAT: deterministic discovery of recurring ordered near-miss pairs
(A before B within CHAIN_WINDOW_MINUTES, default 120), grouped by
(routeA, typeA, routeB, typeB) signature. Ordering uses start-event
observed_at (not detection wall-clock). Strength: 1 OBSERVED_ONCE,
2–3 RECURRING, ≥4 STRONG_RECURRING. Same-vehicle pairs excluded
(self-link guard). Stateless computed view — no new tables/migration:
causal_edges is investigation-scoped (FK-bound) and cannot represent
cross-pattern links; reuse its vocabulary (MAY_CONTRIBUTE_TO +
TEMPORALLY_ASSOCIATED_WITH) and reuse pattern-investigation Evidence rows
for grounding. WHY: event→system intelligence differentiator without causal
overclaim. NON-GOALS: causal inference, graph DB, LLM scoring, touching
detection/baselines. API: GET patterns/{id}/chains (since/until/window),
POST patterns/{id}/chains/investigate {chain_key} → validated agent JSON
(ephemeral, unpersisted), causal-certainty language banned.
