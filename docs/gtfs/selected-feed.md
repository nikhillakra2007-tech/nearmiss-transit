# Selected GTFS-RT feed — MBTA (Massachusetts Bay Transportation Authority)
Agency: MBTA · Country: USA · Region: Greater Boston. Terms: public GTFS-RT
provided for developers (mbta.com/developers); keyless endpoints below.
- VehiclePositions: https://cdn.mbta.com/realtime/VehiclePositions.pb
- TripUpdates: https://cdn.mbta.com/realtime/TripUpdates.pb
- Alerts: https://cdn.mbta.com/realtime/Alerts.pb
Auth: none. Rate: poll politely (~30s). Verified 2026-10-04: VP 41 entities,
TU 366 entities, Alerts 95; protobuf decoded with project parser; feed
timestamps ~60–90s ahead of wall clock (quirk noted, tolerated).
Fields: trip_update.stop_time_update.arrival.delay present but 0 across 3069
updates in snapshot (off-peak on-time service) → live snapshot yields no
near-miss; near-miss story uses labelled REPLAY snapshots (never called live).
Snapshots: backend/tests/fixtures/snapshots/mbta-{VehiclePositions,TripUpdates}.pb.
Env: GTFS_REALTIME_URL=<one of above> GTFS_API_KEY=(empty).
Limitations: delay field often 0/unknown; VP feed small at snapshot time;
fingerprint dedupe is per (entity,timestamp,trip,vehicle) — live re-poll with
new timestamps correctly creates new logical events.
