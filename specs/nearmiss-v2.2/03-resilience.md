# 03 Resilience — spec
Purpose: prioritization indicator per route from observed history. Signals
(0–100 stress, capped ratios): frequency min(nm/10,1); recurrence
min(maxRec/6,1); peak min(maxPeak_s/1200,1); recovery min(avgDur_s/1800,1);
chain min(chainOcc/6,1); trend recent-vs-older counts mapped 0/50/100.
Weights 25/20/20/15/10/10 (heuristic, documented). Missing signal →
redistribute weight proportionally (documented strategy). Zero history →
INSUFFICIENT_DATA, no score (absence ≠ resilience). resilience=100−stress,
1-decimal, clamped. Status: <40 OBSERVED_STRESS, 40–70 ELEVATED, ≥70 STABLE
(heuristic bands). Language: "Operational resilience indicator derived from
observed historical behavior"; never safety/accident/failure-probability.
API: GET /api/v1/resilience?since&until&route_id&limit. UI: cards with numeric
score, status text, signal bars with numbers, VIEW PATTERN link.
