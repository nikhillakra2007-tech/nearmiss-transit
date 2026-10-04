# Frontend verification
Render index.html against live API (seeded demo DB): status badge shows;
patterns list non-empty; clicking pattern shows members→investigation→typed
claims→recommendation→intervention→verification chain; empty DB shows empty
states (not blank); feed-down shows FEED_UNAVAILABLE; keyboard tab order sane;
400px width usable; contrast AA on text. Tested via TestClient + manual DOM
review of app.js render functions.
