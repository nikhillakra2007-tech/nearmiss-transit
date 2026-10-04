"""Inspect a GTFS-RT feed (fetch + decode summary, no persistence).
Usage: python scripts/inspect_feed.py --url <feed> [--api-key KEY]"""
import argparse
import asyncio
import sys
sys.path.insert(0, ".")
from backend.app.services.ingestion.gtfs_client import fetch_feed
from backend.app.services.ingestion.gtfs_parser import parse_feed

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--api-key", default="")
    args = ap.parse_args()
    raw = asyncio.run(fetch_feed(args.url, args.api_key or None))
    rows = parse_feed(raw)
    print(f"entities={len(rows)} kinds={sorted({r.get('kind') for r in rows})}")
    for r in rows[:5]:
        print(r)
