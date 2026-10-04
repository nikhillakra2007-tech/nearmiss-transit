# Feed assumptions

Feeds vary in completeness; missing trip/vehicle/timestamp tolerated; stale
feeds accepted with timestamp; duplicates detected via fingerprint; failures
logged per entity, never crash the cycle; unavailable feed => FEED_UNAVAILABLE.
