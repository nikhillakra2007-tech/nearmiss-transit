# Data model — 15 entities, UUID PKs, external GTFS IDs, JSONB-variant semi-structured fields.
# All history tables: no ON DELETE CASCADE (auditable). Indexes on observed_at,
# agency/route/trip/vehicle/stop, event_type, near_miss.status, pattern.status,
# pattern.last_seen_at, investigation.status + composites (agency,observed_at),
# (route,observed_at), (pattern,created_at).

Entities: Agency(external_id,name,timezone,urls) / Route(agency,external_route_id,
short/long/type,metadata) / Stop(agency,external_stop_id,name,lat/lon) /
Trip(route,external_trip_id,service_date,direction,start_time) /
Vehicle(agency,external_vehicle_id,label) /
TransitEvent(agency,route?,trip?,vehicle?,stop?,event_type enum,observed_at,
scheduled_at?,delay_seconds?,lat/lon?,status,source,source_event_id UNIQUE,
raw/normalized JSONB) /
ServiceAlert(agency,route?,external_alert_id,header/desc/severity,active window) /
NearMiss(agency,route?,trip?,vehicle?,start/recovery events,detected_at,type,
severity,baseline/abnormal JSONB,recovery_duration,confidence,status enum,
detection_reason) / Pattern(agency,route?,type,title/desc,recurrence_count,
first/last_seen,severity,confidence,status,features) /
NearMissPattern(m2m, UNIQUE pair) / Investigation(pattern,status,started/completed,
summary,confidence) / Evidence(investigation,type,source_entity/type/id,desc,
observed_at,payload,confidence) / CausalEdge(investigation,src/dst evidence,
relationship,confidence,explanation — HYPOTHESIS only) /
Recommendation(investigation,type,title/desc/rationale/expected_effect,confidence,
status) / Intervention(recommendation,type,target,requested/approved/executed,
execution_status,execution_result) / Verification(intervention,started/ended,
baseline/post metrics,outcome enum,confidence,explanation).
