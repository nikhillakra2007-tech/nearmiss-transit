# Frontend spec — product story, not a bus map
WHAT: static dependency-free dashboard served by FastAPI at `/` (ADR-006:
zero build, judging-friendly; same /api/v1 contract allows later Next.js).
Sections: system status (live/replay badge) → recurring near-misses →
near-miss detail+timeline → pattern investigation (FACT/INFERENCE/HYPOTHESIS)
→ agent recommendation → intervention/handoff → verification before/after.
WHY: make the agent loop legible. NON-GOALS: route planner, chatbot, map-first
eye candy (map only if it explains the near-miss — deferred). SUCCESS: all
slices render from live API in both modes; error/empty/stale states handled.
