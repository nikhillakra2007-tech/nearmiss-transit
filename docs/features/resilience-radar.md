# Resilience Radar
Purpose: per-route prioritization from observed history. Signals (0–100
stress, capped): frequency nm/10; recurrence maxRec/6; peak maxPeak/1200s;
recovery avgDur/1800s; chain occ/6; trend recent-vs-older. Weights
25/20/20/15/10/10 (heuristic, documented in services/resilience/radar.py).
Missing signal → weight redistributed; zero history → INSUFFICIENT_DATA
(absence ≠ resilience). resilience=100−stress (1-decimal, clamped);
bands <40 OBSERVED_STRESS, 40–70 ELEVATED, ≥70 STABLE. Language: operational
resilience indicator — never safety/accident/failure-probability. API: GET
/api/v1/resilience?since&until&route_id&limit. Example: route42 16.7
OBSERVED_STRESS. UI: cards with numeric score, status text, signal bars.
