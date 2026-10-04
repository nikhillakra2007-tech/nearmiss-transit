# 01 Multi-hop domino — spec (PRIORITY 1)
Purpose: recurring temporal sequences A→B→C (default MAX_CHAIN_DEPTH=3 edges,
setting CHAIN_MAX_DEPTH) built ONLY from valid pairwise occurrence edges
(candidate_pairs: window, ordering by start-event observed_at, same-vehicle
exclusion). Extension rule: edge2.a.id == edge1.b.id, no repeated near-miss
or repeated route in a trail (self-loop/cycle rejection). Grouped by route
sequence; strength via strength_of; deterministic order (occurrences desc,
then key); stateless/idempotent. Evidence: union of Evidence rows for
endpoint near-misses across investigations (helper evidence_for_nm);
multi-hop chains with zero evidence excluded. Vocabulary unchanged
(MAY_CONTRIBUTE_TO, temporal association, not causation). API (additive):
GET /api/v1/patterns/{pattern_id}/multihop → {pattern_id, chains:
[{route_sequence, depth, strength, occurrences, avg_gaps, nodes, hops,
evidence_ids}], disclaimer}. No schema/migration; no detector changes.
UI: vertical node/gap rendering in OPERATIONAL CHAIN section + why-panel +
same disclaimer. Demo: seed route 8 lagging 17 by ~10 min × 4 windows
(42→17→8 STRONG_RECURRING).
