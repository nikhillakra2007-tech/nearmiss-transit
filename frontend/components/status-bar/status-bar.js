/* Status bar component: system health, operational mode, and manual ingestion trigger */

async function refreshStatus() {
  try {
    const h = await jget("/health");
    MODE = h.demo_mode ? "REPLAY" : "LIVE";
    const badge = $("mode-badge");
    if (MODE === "LIVE") {
      badge.innerHTML = `<span class="dot" style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#3fb950;margin-right:6px"></span>LIVE`;
      badge.className = "badge live";
    } else {
      badge.innerHTML = `<span class="dot" style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#d29922;margin-right:6px"></span>HISTORICAL REPLAY`;
      badge.className = "badge replay";
    }
    $("feed-state").textContent =
      "Feed: " + (h.feed === "FEED_UNAVAILABLE" ? "unavailable (replay OK)" : h.feed);
    if (!$("last-update").textContent || $("last-update").textContent === "Last update: —") {
      $("last-update").textContent = "Last update: " + new Date().toLocaleTimeString();
    }
  } catch {
    $("feed-state").textContent = "Feed: backend unreachable";
  }
}

function initIngestionTrigger(onCycleComplete) {
  const btn = $("ingest-btn");
  if (!btn) return;
  btn.addEventListener("click", async (ev) => {
    if (btn.disabled) return;
    btn.disabled = true;
    const originalText = btn.textContent;
    btn.textContent = "Running ingestion cycle…";
    try {
      const now = Math.floor(Date.now() / 1000);
      const simulatedRows = [
        { route_id: "42", vehicle_id: "V42-" + (now % 1000), trip_id: "T42-" + now, delay: 115, kind: "trip_update", timestamp: now },
        { route_id: "Green-E", vehicle_id: "VGLE-" + (now % 1000), trip_id: "TGLE-" + now, delay: 90, kind: "trip_update", timestamp: now },
        { route_id: "39", vehicle_id: "V39-" + (now % 1000), trip_id: "T39-" + now, delay: 85, kind: "trip_update", timestamp: now },
        { route_id: "1", vehicle_id: "V1-" + (now % 1000), trip_id: "T1-" + now, delay: 120, kind: "trip_update", timestamp: now },
        { route_id: "66", vehicle_id: "V66-" + (now % 1000), trip_id: "T66-" + now, delay: 75, kind: "trip_update", timestamp: now },
        { route_id: "Red", vehicle_id: "VRL-" + (now % 1000), trip_id: "TRL-" + now, delay: 55, kind: "trip_update", timestamp: now }
      ];
      await fetch(API + "/ingestion/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ demo_rows: simulatedRows })
      });
      $("last-update").textContent = "Last update: " + new Date().toLocaleTimeString();
      if (typeof onCycleComplete === "function") {
        await onCycleComplete();
      }
    } catch {
      $("feed-state").textContent = "Feed: ingestion trigger failed";
    } finally {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  });
}
