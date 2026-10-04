# F-03 spec — near-miss overview cards (frontend-only, backend frozen)
WHAT: new "Active near-misses" section rendering one card per pattern member
from existing endpoints: patterns list → per-pattern detail (members carry
delay_series, abnormal_value, recovery_event, detected_at). Route names via
/routes lookup map. Recurrence = parent pattern.recurrence_count + title (no
frontend computation). WHY: answer "what is going wrong / one-off or recurring"
in seconds. NON-GOALS: new endpoints, interpolation, hardcoded values, F-02 restyle.
SUCCESS: cards from live API; progression strip + SVG sparkline from real
delay_series only; honest fallback when empty; states preserved; a11y kept.
