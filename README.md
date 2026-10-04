# NearMiss Transit

**An evidence-grounded operational intelligence system that discovers recurring transit problems that almost become disruptions.**

## Problem

Transit systems react after failures happen. NearMiss Transit focuses on what *almost* went wrong — recurring operational near-misses that escalate and recover before becoming full disruptions.

## What It Does

DETECT → REMEMBER → CONNECT → FORECAST → EARLY-WARNING REPLAY → SIMULATE → RECOMMEND → VERIFY

- **Operational Near-Miss Detection** — deviation + escalation + recovery (never bare `delay > X`)
- **Operational Fingerprint** — deterministic signature + similarity (never "root cause")
- **Multi-Hop Domino** — recurring temporal sequences like 42 → 17 → 8 (never proven causation)
- **Emerging Near-Miss Signal** — deterministic early-warning heuristic (never guaranteed prediction)
- **Counterfactual Lab** — hypothetical replays of observed data (never real-world prediction)
- **Intervention Sandbox** — ranked modeled improvements → recommendation → `PENDING_EXTERNAL_ACTION` handoff
- **Resilience Radar** — historical stress prioritization (never safety scoring)
- **Evidence-grounded agent** — FACT / INFERENCE / HYPOTHESIS (+SIMULATION for hypotheticals), every claim traceable

## Why It Is Different

This is NOT "ChatGPT over transit data." Detection, recurrence, chains, scores, and simulations are deterministic and auditable. AI investigates and explains evidence; it never computes facts, never invents evidence, and never claims external actions occurred.

## Architecture

```
GTFS-RT
   ↓
INGESTION
   ↓
NORMALIZED EVENTS
   ↓
NEAR-MISS DETECTION
   ↓
PATTERN MEMORY
   ↓
┌────────────┬─────────────┬──────────────┐
│ Fingerprint│ Multi-Hop   │ Forecast     │
│            │ Domino      │              │
└────────────┴─────────────┴──────────────┘
               ↓
       COUNTERFACTUAL LAB
               ↓
     INTERVENTION SANDBOX
               ↓
        AI INVESTIGATION
               ↓
        RECOMMENDATION
               ↓
          VERIFICATION
```

Full diagram: `docs/architecture/system-overview.md`. Specs: `specs/`.

## Demo (REPLAY, offline-safe)

```powershell
$env:DATABASE_URL="sqlite:///./demo.db"; python scripts/prep_demo.py
$env:DEMO_MODE="true"; uvicorn backend.app.main:app --port 8765
```

Open `/`: Route 42 near-miss → fingerprint → 42→17→8 STRONG_RECURRING chain → 71.3 EMERGING forecast → early-warning replay (EMERGING 60 min before the recorded near-miss, `HISTORICAL_REPLAY` mode) → counterfactual → sandbox best → handoff → verification. Full script: `docs/demo/demo-script.md`.

## LIVE vs REPLAY

LIVE = real GTFS-RT observations (MBTA keyless feeds; `GTFS_REALTIME_URL`). REPLAY = deterministic labelled fixtures. The badge is unmistakable; replay is never called live. Live MBTA snapshots observed so far are all-on-time (zero delays → honestly zero near-misses).

## Tech Stack

Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL (prod) / SQLite (dev/test), httpx, gtfs-realtime-bindings, pytest. Frontend: dependency-free static app served by the backend (ADR-006). No Redis/Kafka/Celery/ML/graph DB.

## Limitations (honest)

Heuristic weights/bands (not learned); replay cascades are not live cascades; simulations/verifications compare observed data only; interventions stay `PENDING_EXTERNAL_ACTION` without a real agency API; sandbox Postgres is an owner/deployment action (`alembic upgrade head` verified via `--sql`).
