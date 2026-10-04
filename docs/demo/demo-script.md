# Demo script (3–5 min, deterministic)
1. Open `/` — status badge shows LIVE (or REPLAY, labelled). 2. "Run ingestion
cycle" → operations table fills. 3. Patterns: "Recurring delay instability
(3x)" — open it. 4. Timeline: peak 1100s → recovered 200s (deviation →
escalation → recovery). 5. Evidence list + typed claims (FACT vs INFERENCE vs
HYPOTHESIS — point at the colors). 6. Agent recommendation. 7. Intervention:
PENDING_EXTERNAL_ACTION — "we record the handoff, we don't pretend to run the
MBTA". 8. Verification before/after. 9. WOW MOMENT — scroll to OPERATIONAL
CHAIN: "We found another pattern — Route 42 near-misses repeatedly precede
Route 17 near-misses (STRONG_RECURRING, 4 windows, ~12 min gaps)." Open "Why is
this connected?", click evidence, INVESTIGATE CHAIN (FACT/INFERENCE/HYPOTHESIS),
then EARLY-WARNING REPLAY: "Would this signal have appeared early enough to
matter?" — HISTORICAL REPLAY badge, EMERGING 60 minutes before the recorded
near-miss, timeline table + signal breakdown. Then show recommendation. Close: "Instead of waiting for a transit
failure, NearMiss finds the situations that repeatedly almost become one."
Fallback: if live feed is down, REPLAY badge shows — same story, honestly labelled.
