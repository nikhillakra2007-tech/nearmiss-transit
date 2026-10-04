# Early-warning replay (V2.6)

Question answered: "Could NearMiss Transit have recognized the developing
operational stress before the near-miss occurred?"

Mechanism: for a pattern's latest historical near-miss, the existing
deterministic forecast (`forecast_pattern`, six weighted signals, missing
redistribution, bands 30/60) is re-evaluated at earlier cutoffs across a
lookback window (default 60 min, step 15; caps 1..180 / >= 5). Every cutoff
passes only its own timestamp into the forecast, which filters all inputs
to `observed_at <= cutoff` — future observations cannot influence earlier
points (regression-tested). No new tables, no new scoring, no ML.

Output: per-cutoff score/band/signal contributions, `first_watch` and
`first_emerging` (null when never crossed — never zero), target id +
timestamp, available-history counts, and a HISTORICAL_REPLAY disclaimer.
Zero in-scope members → honest INSUFFICIENT_DATA, never a fabricated
timeline.

Demo: Route 42 pattern replays EMERGING (61.7) a full hour before the
recorded near-miss, rising to 71.3 at the event — shown with the
HISTORICAL REPLAY badge, a vertical timeline, a text table alternative,
and a per-cutoff signal breakdown. Historical validation, not a claim of
future prediction accuracy.
