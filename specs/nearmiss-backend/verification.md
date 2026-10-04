# Verification — 20 backend success checks
1. Postgres/SQLite engine starts. 2. Alembic upgrade head from clean DB.
3. GTFS fetch (or FEED_UNAVAILABLE clearly marked). 4. Parse valid/malformed fixtures.
5. Normalized events stored. 6. Duplicate feed → no new rows (source_event_id).
7. State reconstruction (position/route/trip/delay/recent). 8. Delay cases
(zero/pos/neg/missing/tz). 9. Near-miss needs deviation+escalation+recovery.
10. Recurrence → pattern (≥3). 11. Pattern → investigation. 12. Evidence bundle.
13. Mock agent reasons. 14. Hallucinated evidence IDs rejected. 15. Recommendation.
16. Intervention PROPOSED/PENDING (never fake execution). 17. Verification
before/after → 4 outcomes. 18. Full /api/v1 lifecycle. 19. pytest green.
20. Docs complete. Run: `pytest backend/tests -q` + `python scripts/inspect_feed.py --help`.
