# 5-minute demo script (REPLAY, offline-safe)
0:00–0:30 Problem + pitch: "NearMiss Transit discovers recurring transit
problems that almost become disruptions — then connects, forecasts,
simulates, recommends, and verifies." Show REPLAY badge.
0:30–1:00 DETECT: Route 42 card — delay progression + recovery. "Something
almost failed — but recovered."
1:00–1:30 REMEMBER: fingerprint chips + 75%-similar Route 17 pattern.
1:30–2:00 CONNECT: 42→17→8 STRONG_RECURRING ×4, gaps 12/12. "Temporal
relationship, not proven causation." Open WHY, click evidence.
2:00–2:30 FORECAST: 71.3 EMERGING + signal contributions.
2:30–2:50 EARLY-WARNING REPLAY: "But would this signal have appeared early
enough to matter?" Open Early-Warning Replay (HISTORICAL REPLAY badge) —
forecast already EMERGING 60 minutes before the recorded near-miss, rising
to 71.3 at the event. Show the timeline table + FIRST EMERGING marker, then
the per-cutoff signal breakdown.
2:30–3:15 SIMULATE: Counterfactual Lab observed vs simulated + banner.
3:15–4:00 SANDBOX: compare three, BEST MODELED INTERVENTION, create
recommendation.
4:00–4:30 INVESTIGATE + RECOMMEND: FACT/INFERENCE/HYPOTHESIS, handoff →
PENDING_EXTERNAL_ACTION ("we don't pretend to run the MBTA").
4:30–5:00 VERIFY: before/after outcome. Closer: "Instead of waiting for a
transit failure, NearMiss finds the situations that repeatedly almost
become one."
Setup: DATABASE_URL=sqlite:///./demo.db python scripts/prep_demo.py, then
DEMO_MODE=true uvicorn backend.app.main:app --port 8765.
