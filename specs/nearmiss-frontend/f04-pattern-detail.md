# F-04 spec — pattern detail hero (frontend-only, backend frozen)
WHAT: upgrade `openPattern` into the hero screen: header (title/route/type/
recurrence/derived hour-window/status + mode context), per-occurrence blocks
each with SVG delay-vs-time chart (real delay_series only, peak + recovery
markers, baseline-median dashed line only when baseline_value present),
generated textual summary, evidence timeline from real start/peak/recovery
points with source IDs, back-to-overview + focus management, exact state
strings. WHY: make NORMAL→…→RECOVERY and "this happened repeatedly" obvious.
NON-GOALS: chart lib, maps, new endpoints, invented labels/values.
SUCCESS: all visuals trace to detail payload; empty/missing handled honestly.
