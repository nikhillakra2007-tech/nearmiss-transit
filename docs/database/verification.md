# Database verification (Stage 1 record)
SQLite: 39/39 tests incl. duplicate-source rejection, FK-invalid documented,
history-preservation (no cascade deletes in repositories), JSON roundtrip.
Postgres: server starts in sandbox but backends crash on connect (Windows
session shared-memory issue, pg logs 0xC0000142/487 — environment, not app).
Migration validated via `alembic upgrade head --sql` against PostgresqlImpl:
17 CREATE TABLEs, no errors. Production path: managed Postgres + same migration.
Stage 1: YELLOW (only blocker is sandbox PG; all app-side checks GREEN).
