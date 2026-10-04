# Agent contract — LLM reasons over deterministic evidence only.
Input: {pattern, baseline, recurrence, near_misses[], timeline[], alerts[], evidence[]}.
Output JSON: {summary:str, claims:[{type: FACT|INFERENCE|HYPOTHESIS, statement,
 evidence_ids[], confidence 0..1}], possible_causes[], recommendation:{title,
 description, expected_effect, confidence}}.
Rules: FACT needs ≥1 valid evidence_id; every evidence_id must exist in bundle;
 no new route/stop/event IDs; delays/baselines quoted must match bundle (±tolerance);
 malformed/unknown-ID output rejected → investigation stays OPEN with error logged.
Tools (no direct DB): get_pattern, get_near_misses, get_event_timeline,
 get_route_history, get_stop_history, get_baseline, get_service_alerts,
 compare_periods, create_recommendation, create_intervention, request_verification.
Provider: {generate(bundle)->dict}; MockProvider deterministic summary;
 env LLM_PROVIDER/KEY/MODEL select real provider (not required for tests).
