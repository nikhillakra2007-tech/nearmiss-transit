# E2E validation (2026-10-04, DEMO/REPLAY on scratch sqlite e2e.db)
Chain: seed 3 vehicles × delay-spike series → 3 near-misses (peak 1100s,
recovered to 200s) → 1 pattern (recurrence 3) → investigation + evidence →
MockProvider agent → recommendation → intervention PENDING_EXTERNAL_ACTION →
verification INSUFFICIENT_DATA (windows outside seeded span — honest outcome).
IDs: agency 29b5a787-fae2-4cf5-bc2a-37306418ad89 · near-miss
3136c768-bbb0-4f78-8b8f-89046aeb2f2e · pattern 5db548a2-58f4-41bc-90f9-d33d8be709f2 ·
investigation 624c0d72-1ef0-43a6-a90d-cde20177f669 · recommendation
5573e0fd-3510-42b0-b966-6980109b738c · intervention 9ee7581d-e715-4e7f-b018-91280100e7ac ·
verification 31df1884-68ac-4165-859f-432be01e6cd8.
Live-data check (stage3_real.db, MBTA snapshot): 42 vehicles, 418 events,
230 delay readings all 0s → 0 near-misses (correct true negative, no false positives).
Frontend: `/` serves dashboard; `/api/v1/patterns/{id}/detail` returns the
whole chain in one call (covered by test_frontend_integration.py).
