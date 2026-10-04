# API overview

Versioned /api/v1. Resource reads + POST investigations/interventions/
ingestion/run. Pagination limit/offset. Typed errors. CORS restricted.
Demo mode tagged DEMO/REPLAY.
Forecast family: `GET /api/v1/patterns/{id}/forecast?at=` (+explain) and
historical replay `GET /api/v1/patterns/{id}/early-warning?at=&
lookback_minutes=&step_minutes=` (defaults 60/15, caps 1..180 / >= 5,
typed 422; mode HISTORICAL_REPLAY; INSUFFICIENT_DATA stays honest).
