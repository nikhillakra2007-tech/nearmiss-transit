"""GTFS-RT HTTP client: timeout, retry with backoff, validation."""
from __future__ import annotations
import asyncio
import httpx
from backend.app.core.config import settings
from backend.app.core.exceptions import FeedUnavailableError
from backend.app.core.logging import get_logger

log = get_logger("gtfs_client")


async def fetch_feed(url: str | None = None, api_key: str | None = None, timeout_s: int | None = None) -> bytes:
    target = url or settings.GTFS_REALTIME_URL
    if not target:
        raise FeedUnavailableError("GTFS_REALTIME_URL is not configured (FEED_UNAVAILABLE)")
    headers = {}
    key = api_key if api_key is not None else settings.GTFS_API_KEY
    if key:
        headers["Authorization"] = key
    timeout = timeout_s or settings.FEED_TIMEOUT_SECONDS
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            log.info(f"feed_fetch_started attempt={attempt}")
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(target, headers=headers)
                resp.raise_for_status()
                log.info("feed_fetch_completed bytes=%d" % len(resp.content))
                return resp.content
        except Exception as exc:
            last_exc = exc
            log.warning(f"feed_fetch_failed attempt={attempt} err={exc}")
            await asyncio.sleep(2 ** attempt)
    raise FeedUnavailableError(f"Feed unavailable after retries: {last_exc}")
