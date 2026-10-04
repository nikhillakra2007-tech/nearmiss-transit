# Deployment (Stage 14)
Backend: Render/Railway/Fly — `uvicorn backend.app.main:app`, env: DATABASE_URL
(managed Postgres, e.g. Neon/Supabase), GTFS_REALTIME_URL, GTFS_API_KEY,
LLM_* (optional), LOG_LEVEL, ENVIRONMENT=production, DEMO_MODE=false.
DB: `alembic upgrade head` on first deploy (0001 verified via --sql against
Postgres dialect). Frontend: served by FastAPI `/` (no build step). Health:
GET /api/v1/health. Never commit .env. Smoke (Stage 15): health→ingestion→
events→patterns→detail→intervention→verification, all via TestClient green;
browser check deferred to deploy env.
