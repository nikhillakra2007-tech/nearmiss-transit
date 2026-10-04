# P2 clarifications
- Level: pattern (not route) — reuses fingerprint(pattern), recurrence,
  member evidence, chain exposure without duplication.
- `at` defaults to now; tests pin `at` for leakage/determinism proofs.
- DEVIATION_TREND uses raw route delay events (not near-miss windows) so
  current ramp-ups are visible before any near-miss forms.
- Missing-signal rule: redistribute (resilience convention), but <3 available
  signals → INSUFFICIENT_DATA (forecast needs corroboration by design).
- Agent explain: same provider + safety module; SIMULATION type NOT allowed
  here (only FACT/INFERENCE/HYPOTHESIS) — validate via validate_safe_output
  then reject SIMULATION claims explicitly.
- Demo EMERGING: seed a sub-threshold rising "current ramp" tail on route42
  (peak <600s so no near-miss forms; clearly REPLAY).
- No new tables; no detector/baseline changes; additive endpoint + service.
