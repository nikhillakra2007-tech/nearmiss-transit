# 01 Counterfactual Lab — spec
Purpose: deterministic hypothetical replay of an observed delay_series.
Allow-list: REDUCE_PEAK_PERCENT p∈[1,50]; START_RECOVERY_EARLIER m∈[1,30]min;
REDUCE_RECOVERY_DURATION_PERCENT p∈[1,50]. Inputs strictly validated
(type/range/NaN/Inf/0/negative/unknown scenario/missing NM/empty series →
typed 422). Algorithms (no invention): A scales peak-valued points only;
B shifts post-peak timestamps earlier by m (needs ≥1 post-peak point and
order preserved, else INSUFFICIENT_SIMULATION_RESOLUTION); C compresses
post-peak timestamps toward peak by factor (needs ≥2 post-peak points).
Timestamps otherwise preserved; original untouched. Output: mode
COUNTERFACTUAL, scenario, parameter, original/simulated {series,peak,final,
recovery_duration_seconds}, delta, status SIMULATED|INSUFFICIENT_DATA|
INSUFFICIENT_SIMULATION_RESOLUTION. Ephemeral (no table). API: POST
/api/v1/near-misses/{id}/simulate {scenario,value} (+explain flag → agent
claims with SIMULATION type allowed, evidence-bound, "would have prevented"
banned). UI: selector+param+run, observed vs simulated SVG, deltas, banner
HYPOTHETICAL SIMULATION NOT A PREDICTION. Safety: never prediction/forecast/
guarantee/causal-effect language.
