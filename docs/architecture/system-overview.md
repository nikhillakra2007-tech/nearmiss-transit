# System overview (V2.6)

Modular monolith: `core` / `db` (15 tables) / `schemas` / `repositories` /
`services` (ingestion, transit, detection, patterns, investigation, agent,
recommendations, interventions, verification, chains, counterfactual,
fingerprints, forecast, replay, resilience, sandbox) / `api` (`/api/v1`) /
`workers`.
Static frontend served at `/`.

```mermaid
flowchart LR
  GTFS[GTFS-RT] --> ING[Ingestion\nidempotent]
  ING --> EV[transit_events]
  EV --> STATE[State/Delay/Baseline]
  STATE --> NM[Near-miss\ndeviation+escalation+recovery]
  NM --> PAT[Patterns\nrecurrence]
  PAT --> CH[Chains/Multi-hop\ntemporal]
  PAT --> FP[Fingerprint/Similar]
  PAT --> FC[Forecast\nheuristic]
  FC --> RP[Early-warning replay\nhistorical cutoffs]
  NM --> LAB[Counterfactual]
  LAB --> SB[Sandbox\nranked]
  PAT --> AG[Agent\nFACT/INFERENCE/HYPOTHESIS]
  AG --> REC[Recommendation]
  REC --> IV[Intervention\nPENDING handoff]
  IV --> VER[Verification\nbefore/after]
```

Deterministic system owns facts/scores/simulations; agent explains evidence;
DB is memory; workers observe; verification closes the loop. Live feeds
untrusted input; LLM output untrusted, validated, never executed.
