# Security audit (Stage 13)
Secrets: env-only, .env.example, no keys in code/logs (redact_secrets;
JsonFormatter logs component/message only). Injection: SQLAlchemy ORM only,
no raw SQL; Pydantic validation on writes; 422 on bad input; error handler
returns codes, no stack leak. CORS restricted to localhost:3000. External
content: GTFS/alert text treated as data (adversarial test:
prompt-injection-in-feed stays inert). LLM: MockProvider default; outputs
validated (evidence IDs, claim types, confidence range); never executed;
interventions pass service allow-list (REPROGRAM_TRAFFIC_LIGHTS rejected,
tested). No shell, no dynamic imports, no arbitrary URLs. Privacy: no PII
collected; positions/vehicle IDs operational only. Rate limiting: documented
as deployment concern (reverse proxy) — not in app. Status: GREEN with noted
limitation (no in-app rate limit).
