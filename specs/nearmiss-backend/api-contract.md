# API contract — prefix /api/v1, JSON, pagination ?limit (1..200, default 50) &offset.
GET /health + /api/v1/health → {status, environment, demo_mode, db, feed}
CRUD-read: GET /agencies, /agencies/{id}, /routes[?agency_id], /routes/{id},
 /stops[?agency_id], /stops/{id}, /vehicles[?agency_id], /vehicles/{id},
 /events[?agency_id&event_type&since&until&route_id&vehicle_id],
 /events/{id}, /near-misses[?status&route_id], /near-misses/{id},
 /patterns[?status], /patterns/{id}, /investigations, /investigations/{id},
 /recommendations, /recommendations/{id}, /interventions/{id},
 /verifications/{id}.
Writes: POST /investigations {pattern_id} → creates UNDER_INVESTIGATION (idempotent
 active reuse); POST /interventions {recommendation_id,type,target}; POST
 /ingestion/run {agency_id?, max_entities?} → {fetched,ingested,duplicates,errors}.
Errors: typed → 404 ENTITY_NOT_FOUND, 409 DUPLICATE/ACTIVE_EXISTS, 502
 FEED_UNAVAILABLE/FEED_PARSE, 422 validation, 500 internal (no stack leak).
Demo header: X-Demo-Mode: replay when DEMO_MODE=true.
