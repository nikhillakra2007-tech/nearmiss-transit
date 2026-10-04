# 02 Fingerprints — spec
Purpose: deterministic operational signature per pattern from verified fields
only. Buckets (centralized): time NIGHT0-5/MORNING5-11/MIDDAY11-16/EVENING16-21/
LATE21-24 (hour of first_seen_at); peak LOW<5/MODERATE5-10/HIGH10-20/EXTREME>20
min (max member peak); recovery FAST<5/MODERATE5-10/SLOW>10 min (mean duration,
UNKNOWN if none); recurrence via chains.strength_of; type=pattern_type;
route=external id; chain_exposure bool via pattern_chains. Canonical id
"route|TIME|type|PEAK|RECOVERY|STRENGTH|CHAIN|NOCHAIN". Similarity weights:
route20/type20/time15/peak15/recovery15/recurrence10/chain5; classes
HIGH≥80/PARTIAL50–79/LOW<50 ("OPERATIONAL SIGNATURE SIMILARITY", never root
cause/confidence). API: GET patterns/{id}/fingerprint, GET .../similar?n=5
(self excluded, similarity desc, id tiebreak, matched[] list). UI: chips +
similar list with ✓ matched features + VIEW PATTERN (opens detail).
