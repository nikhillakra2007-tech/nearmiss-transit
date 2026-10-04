# Operational Fingerprints
Purpose: deterministic signature per pattern from verified fields. Buckets
(services/fingerprints/engine.py): time NIGHT/MORNING/MIDDAY/EVENING/LATE;
peak LOW<5/MODERATE≤10/HIGH≤20/EXTREME>20 min; recovery FAST<5/MODERATE≤10/
SLOW>10 min (UNKNOWN if none); recurrence via chain strength; route external
id; chain_exposure via pattern_chains. Canonical id joined with "|".
Similarity weights route20/type20/time15/peak15/recovery15/recurrence10/
chain5 (constants, not learned); HIGH≥80/PARTIAL50–79/LOW<50 — OPERATIONAL
SIGNATURE SIMILARITY, never root cause/confidence. API: GET
patterns/{id}/fingerprint, GET .../similar?n=5 (self excluded, similarity
desc, id tiebreak, matched[]). Example: route17 vs route42 → 75% PARTIAL
(type+time+peak). UI: chips + similar cards with ✓ matched + VIEW PATTERN.
