# Frontend completion (F-02–F-10)
A. Architecture: static index.html/styles.css/app.js (ADR-006), served by
FastAPI `/`, centralized jget/jpost, zero dependencies, 30s status poll only.
B. Slices: F-02 shell/nav/status/freshness; F-03 near-miss cards + sparklines;
F-04 pattern hero + SVG timelines + baseline + evidence timeline; F-05 claims +
traceable evidence; F-06 rec + copy + record-handoff; F-07 verification visual;
F-08 differentiated states; F-09 a11y/responsive; F-10 integrated demo chain.
C. APIs: health, routes, patterns, patterns/{id}/detail, events/{id},
near-misses/{id}, POST ingestion/run, POST interventions (all existing).
D. Screens: status header, near-miss cards, pattern detail (occurrences,
investigation, recommendation, intervention, verification), ops table.
E. A11y: semantic landmarks, skip link, focus management, labels, aria-live,
SVG titles + text alternatives, no color-only meaning, keyboard-native controls.
F. Responsive: stacking cards, fluid SVG, scrollable tables, 40rem breakpoint.
G. Errors: 404/422/500/network differentiated; empty/insufficient/unavailable
states; no stack traces; double-submit guarded mutations.
H. LIVE/REPLAY: badge + per-detail mode line; replay never called live.
I. Demo: 19-step chain validated against seeded API incl. record + re-fetch.
J. Limitations: verbatim claim texts not persisted (rendered from record;
documented in UI fineprint); alert trace limited to stored fields; no browser
automation in this env (static + API-level verification instead).
L. V2 domino: OPERATIONAL CHAIN section in pattern detail (strength badge,
why-panel, investigate-chain, window compare); chain agent claims + rec;
see docs/features/operational-domino.md.
M. V2.2: Counterfactual Lab (scenario/param/run, observed vs simulated,
banner, agent explain), fingerprint chips + similar patterns, resilience
radar cards; see docs/features/*.md and docs/final/v2.2-validation.md.
K. Deployment: frontend ships with backend (no separate deploy).
