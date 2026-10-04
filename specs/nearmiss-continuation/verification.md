# Continuation verification (per-stage gates)
S0: pytest 22/22 + compileall + imports + FastAPI startup. S1: pg initdb/start,
alembic upgrade head on clean DB, tables/indexes/FK/unique checks, duplicate-FK
rejection tests. S2: HTTP 200 + protobuf decode + entity counts + timestamp
freshness, feed doc. S3: rows persisted, rerun dedupes, malformed isolated.
S4: detector output on real data OR labelled replay near-miss. S5: pattern→rec
chain with evidence IDs. S6: adversarial agent tests green, LLM-off path works.
S7: PENDING_EXTERNAL_ACTION enforced; 4 verification outcomes reachable. S8-10:
frontend renders all slices against live API in both modes. S11: e2e doc with
real IDs. S12-13: keyboard/contrast audit + security checklist. S15: health→verify
smoke green.
