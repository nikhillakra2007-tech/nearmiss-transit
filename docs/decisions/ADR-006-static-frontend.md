# ADR-006 static frontend over Next.js
Chosen: dependency-free static frontend served by FastAPI. Reasons: zero build
step (judging-friendly), Node build fragility avoided, same /api/v1 contract
so Next.js can replace it later without backend changes. Map deferred:
timeline table explains near-misses better than dots on a map. Status: accepted.
