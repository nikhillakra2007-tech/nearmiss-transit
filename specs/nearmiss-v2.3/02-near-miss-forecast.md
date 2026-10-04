# 02 Near-miss forecast — spec (PRIORITY 2)
Problem: operators see near-misses only after recovery; need an early-warning
signal when current behavior resembles historical near-miss conditions.
Goals: deterministic 0–100 EMERGING_SIGNAL_SCORE per pattern with statuses
INSUFFICIENT_DATA / NORMAL / WATCH / EMERGING; fully explainable signals;
evidence-linked; no future leakage (all inputs filtered to evaluated_at `at`).
Non-goals: ML, LLM scoring, safety/failure prediction, new tables.
Inputs: pattern members + route delay events (observed_at ≤ at) + fingerprint
+ chains + member evidence. Signals/weights (sum 100, missing redistributes,
<3 available → INSUFFICIENT_DATA): DEVIATION_TREND 25 (recent-vs-older median
via median_baseline; ≥6 points), RECOVERY_WEAKENING 20 (recent vs historical
avg duration; ≥3 durations), RECURRENCE 15 (min(rec/6,1)), FINGERPRINT_SIM 15
(max similar score; needs ≥1 other pattern), CHAIN_EXPOSURE 15
(min(chain_occ/6,1)), RECENT_STRESS 10 (recent-quarter member fraction).
Score bands: <30 NORMAL, 30–60 WATCH, >60 EMERGING (heuristic, documented).
Zero history → INSUFFICIENT_DATA (never 0). API: GET
patterns/{id}/forecast?at= (+explain → agent FACT/INFERENCE/HYPOTHESIS over
evidence, extended bans: will fail/guarantee/unsafe/dangerous/accident).
Frontend: overview EMERGING cards + why-expandable + disclaimer + View pattern.
Evidence: member Evidence IDs per signal. Safety: banned prediction language;
LLM explains only. Limitations: heuristic weights; replay demo tail may be
needed for EMERGING example; live honesty preserved. Tests: 24-item plan
(mapped in tasks).
