# Ingestion

httpx fetch with timeout/retry/backoff; protobuf decode; per-entity error
isolation; normalize to internal event; idempotent persist on
(agency_id, source_event_id). Retention via EVENT_RETENTION_DAYS.
