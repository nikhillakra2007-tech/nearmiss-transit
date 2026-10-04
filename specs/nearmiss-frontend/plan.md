# Frontend plan — static app, 8 slices mapped to page sections
stack: index.html + styles.css + app.js (no build). lib: Api client wrapper
around /api/v1 with mode badge. components (sections): status, patterns,
nearmiss detail, investigation, recommendation, verification. hooks: poll
health/ingestion every 30s. Slices 1-7 → sections; slice 8 map → deferred
(table timeline explains better; documented). Integration: full-row resource
serialization + /detail chain endpoints (backend change, justified by contract).
