from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT,
            "demo_mode": settings.DEMO_MODE, "db": "configured", "feed": "configured" if settings.GTFS_REALTIME_URL else "FEED_UNAVAILABLE"}
