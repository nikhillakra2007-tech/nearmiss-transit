# P1 plan
1. config CHAIN_MAX_DEPTH=3 (additive). 2. services/chains/multihop.py:
build_trails (DFS ≤ depth over pair occurrences), group by route sequence,
evidence union, exclusion rules. 3. Reuse candidate_pairs/_start_time/
strength_of/_member_evidence_ids (add evidence_for_nm helper in detector).
4. Route in chains.py router: GET multihop. 5. Tests: 2-hop/3-hop/max/exceed/
self-loop/dup-node/order/missing-evidence/same-vehicle/boundary/±1s/strength/
order/idempotency. 6. Seed route 8 (REPLAY, labelled). 7. Frontend chain
section extension. 8. Docs + demo validation + full suite.
