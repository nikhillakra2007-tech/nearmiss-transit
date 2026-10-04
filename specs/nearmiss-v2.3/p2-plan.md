# P2 plan
1. services/forecast/engine.py: evaluated_at filtering (_naive), six signals
   reusing median_baseline/_cap-style/strength/fingerprint/similar/chain
   detector/member-evidence; bands; explain via provider+safety.
2. routes: GET patterns/{id}/forecast (?at, ?explain) in v22.py or chains.py
   (follow forecast home: new routes/forecast.py? — put in v22.py to avoid
   file sprawl; document).
3. Tests (24): trend up/flat/down, recovery weak/stable, recurrence,
   fingerprint, chain, recent stress, insufficient/zero history, missing 1/N,
   boundaries (0/30/60/100 clamp), determinism, no-leakage (T1 stable after
   T2 insert), bad timestamps/UUIDs/dupes, evidence IDs, invalid params,
   adversarial phrases, LIVE-honest (all-zero delays → INSUFFICIENT/NORMAL).
4. Seed emerging tail + prep_demo reuse. 5. Frontend overview cards.
6. Docs + full suite + gate.
