/* Operations live component: GTFS route/vehicle telemetry and recent events stream */

async function refreshOps() {
  const box = $("ops");
  if (!box) return;
  try {
    const [events, vehicles, routes] = await Promise.all([
      jget("/events?limit=25"),
      jget("/vehicles?limit=100"),
      jget("/routes?limit=100"),
    ]);
    box.innerHTML = `<table><tr><th scope="col">Routes Monitored</th><th scope="col">Active Vehicles</th><th scope="col">Recent Delay Events</th></tr>
      <tr><td>${routes.length}</td><td>${vehicles.length}</td><td>${
      events.length
    } observed</td></tr></table>
      <table><tr><th scope="col">Observed at</th><th scope="col">Route</th><th scope="col">Type</th><th scope="col">Delay (s)</th></tr>
      ${events
        .map((e) => {
          const d =
            e.delay_seconds != null
              ? `${e.delay_seconds}s`
              : e.raw_payload && e.raw_payload.delay_seconds != null
              ? `${e.raw_payload.delay_seconds}s`
              : e.raw_payload && e.raw_payload.delay != null
              ? `${e.raw_payload.delay}s`
              : "Normal (0s)";
          const isDelayed = typeof d === "string" && !d.startsWith("Normal");
          const routeLabel = e.route_id || (e.raw_payload && e.raw_payload.route_id) || "System";
          return `<tr><td>${esc(e.observed_at)}</td><td><strong>${esc(routeLabel)}</strong></td><td>${esc(
            e.event_type
          )}</td><td><span class="${isDelayed ? "sev MEDIUM" : ""}">${esc(d)}</span></td></tr>`;
        })
        .join("")}</table>`;
    const latest = events
      .map((e) => e.observed_at)
      .filter(Boolean)
      .sort()
      .pop();
    if (latest) {
      const isoStr =
        latest.endsWith("Z") || latest.includes("+") ? latest : latest + "Z";
      const diffMs = Date.now() - new Date(isoStr).getTime();
      const mins = Math.max(0, Math.round(diffMs / 60000));
      $("freshness").textContent =
        mins < 2 ? "Data freshness: just now" : `Data freshness: ${mins} min ago`;
    }
  } catch {
    box.innerHTML = `<p class="empty">Operations unavailable.</p>`;
  }
}
