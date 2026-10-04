# F-01 frontend audit — verdict: YELLOW (extend, do not rebuild)
Architecture: static dependency-free (index.html + styles.css + app.js, no
build), served by FastAPI `/`; centralized `jget` API client; all dynamic
output via `esc()` (no innerHTML injection of untrusted HTML — XSS posture
good); semantic sections, aria-live status, focus-visible, responsive CSS.
What works (preserve): mode badge LIVE/REPLAY, Ops table, pattern cards,
detail chain (members→evidence→recommendation→intervention→verification),
empty/error placeholders, 30s polling, honesty strings.
Gaps vs master prompt: (1) no near-miss overview cards with delay progression
(§6B); (2) agent typed claims FACT/INFERENCE/HYPOTHESIS not displayed — evidence
rendered with hardcoded FACT class (§8); (3) no click-to-trace evidence detail
(§9); (4) no investigation queue states (§6D); (5) no SVG delay/baseline/
before-after visuals (§14, dependency-free SVG proposed); (6) errors generic,
no 404/422/500 differentiation (§16); (7) charts will need textual summaries (§19).
Backend endpoints required: all exist (health, resources, detail, ingest,
investigations, interventions). One anticipated need: full per-point delay
series per near-miss for the progression strip (§6B example) — detail endpoint
currently carries start/recovery events only. PROPOSAL (not yet approved):
extend `detail` members with the vehicle's delay series between start and
recovery (read-only, additive field). No backend change until approved.
Slices: F-02 shell/status polish → F-03 near-miss cards → F-04 timeline+SVG →
F-05 claims+trace → F-06 rec/handoff → F-07 verification visual → F-08 states →
F-09 a11y/responsive → F-10 integration/demo. Risks: scope creep into maps
(explicitly deferred); backend freeze respected.
