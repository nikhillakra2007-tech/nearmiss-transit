# Schema

15 entities, UUID PKs, external GTFS IDs, JSONB-variant, explicit FKs, no
cascade on history, indexes on observed_at, agency/route/trip/vehicle/stop,
event_type, near_miss.status, pattern.status/last_seen_at, investigation.status.
See specs/nearmiss-backend/data-model.md.
