# 03 Intervention sandbox — spec
Purpose: compare modeled interventions on observed data and route the best
into the existing recommendation/handoff flow. Reuses counterfactual
transforms verbatim (no duplicated math). Improvement = mean(peak-fraction
gain, duration-fraction gain) as %; deterministic rank (improvement desc,
scenario-name tiebreak); BEST MODELED INTERVENTION language only. API: POST
near-misses/{id}/sandbox {scenarios[]≤5 | presets, explain} → options +
ranking + best + note; POST .../sandbox/recommend {scenario,value} → creates
MODELED_INTERVENTION recommendation on the near-miss's latest investigation
(422 if none) for the existing intervention form (PENDING_EXTERNAL_ACTION).
Agent: ranking explanation with SIMULATION allowed, safety-validated. UI:
lab-result "Compare all three" → table + best + create-recommendation →
detail refresh shows rec + handoff form. Non-simulable options shown as such.
