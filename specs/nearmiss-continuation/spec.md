# Continuation spec — backend foundation → validated MVP + frontend
WHAT: Verify claimed backend (22/22), validate Postgres + real GTFS-RT feed +
real ingestion/detection, harden agent/verification, build frontend, integrate,
e2e-validate, audit, deploy docs, demo. WHY: turn foundation into demonstrable
agent loop. CONSTRAINTS: preserve working backend; modular monolith; no
Redis/Kafka/Celery; no fake live claims; DEMO/REPLAY labelled; secrets in env.
SUCCESS: full chain LIVE/REPLAY→VERIFY works, frontend shows it, tests green,
docs complete. NON-GOALS: microservices, safety prediction, passenger PII,
fake agency control. RISKS: feed instability → replay fallback; no Postgres
server → sqlite fallback documented; live near-miss scarcity → labelled replay.
