# Counterfactual Lab
Purpose: deterministic hypothetical replay of an observed delay_series.
Allow-listed scenarios (centralized in services/counterfactual/lab.py):
REDUCE_PEAK_PERCENT p∈[1,50] (scales peak-valued points only); 
START_RECOVERY_EARLIER m∈[1,30]min (shifts post-peak timestamps; order must
hold); REDUCE_RECOVERY_DURATION_PERCENT p∈[1,50] (compresses post-peak times
toward peak). No invented points; INSUFFICIENT_SIMULATION_RESOLUTION when
resolution lacking; original never mutated. Ephemeral (no table). API: POST
/api/v1/near-misses/{id}/simulate {scenario,value[,explain]} → mode
COUNTERFACTUAL + original/simulated/delta + optional agent claims (SIMULATION
type allowed, evidence-bound, prevention-guarantee language banned). Safety:
hypothetical replay only — never prediction/forecast/guarantee/causal effect.
UI: observed vs simulated SVG, deltas, HYPOTHETICAL SIMULATION banner.
Example: peak 16.7 → 13.3 min at 25%. Demo: any occurrence → Counterfactual Lab.
