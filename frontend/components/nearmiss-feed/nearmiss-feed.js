/* Near-miss feed component: active operational near-misses cards */

async function refreshNearMisses(onOpenPattern) {
  const box = $("nearmisses");
  if (!box) return;
  try {
    const [patterns, routes] = await Promise.all([
      jget("/patterns?limit=20"),
      jget("/routes?limit=200"),
    ]);
    const routeName = {};
    routes.forEach((r) => {
      routeName[r.id] =
        r.short_name || r.long_name || r.external_route_id || "unknown route";
    });
    const targetPatterns = patterns.slice(0, 10);
    const details = await Promise.all(
      targetPatterns.map((p) =>
        jget(`/patterns/${p.id}/detail`).catch(() => null)
      )
    );
    const cards = [];
    const seenRoutes = new Set();
    targetPatterns.forEach((p, idx) => {
      const det = details[idx];
      if (!det || !det.members || !det.members.length) return;
      const members = [...det.members].sort(
        (a, b) => new Date(b.detected_at || 0) - new Date(a.detected_at || 0)
      );
      for (const m of members) {
        const routeKey = m.route_id || p.route_id || p.id;
        if (seenRoutes.has(routeKey)) continue;
        seenRoutes.add(routeKey);

        const series = Array.isArray(m.delay_series) ? m.delay_series : [];
        const peak = series.length
          ? Math.max(...series.map((s) => s.delay_minutes))
          : (m.abnormal_value || {}).peak_delay != null
          ? Math.round((m.abnormal_value.peak_delay / 60) * 10) / 10
          : null;
        const final = series.length
          ? series[series.length - 1].delay_minutes
          : (m.abnormal_value || {}).final_delay != null
          ? Math.round((m.abnormal_value.final_delay / 60) * 10) / 10
          : null;
        const prog = series.length
          ? series.map((s) => s.delay_minutes).join(" → ") + " min"
          : "Insufficient delay-series data";
        const recovered = m.recovery_event_id
          ? `Recovered: yes${
              m.recovery_duration_seconds != null
                ? ` (${m.recovery_duration_seconds}s)`
                : ""
            }`
          : "Recovered: not recorded";
        cards.push(`<article class="card">
          <h3>${esc(routeName[m.route_id] || m.route_id || "Unknown route")}</h3>
          <p><span class="sev ${esc(m.severity)}">${esc(m.severity)}</span> ${esc(
          m.near_miss_type
        )}</p>
          <p class="prog">${esc(prog)}</p>
          ${sparkline(
            series,
            `Delay progression, peak ${peak} minutes, final ${final} minutes`
          )}
          <p>Peak ${esc(peak)} min → final ${esc(final)} min · ${esc(
          recovered
        )}</p>
          <p>Recurring: part of “${esc(p.title)}” · ${esc(
          p.recurrence_count
        )} occurrences · ${esc(m.detected_at)}</p>
          <button type="button" data-open-pattern="${esc(
            p.id
          )}">Open investigation</button></article>`);
      }
    });
    box.innerHTML = cards.length
      ? cards.join("")
      : `<p class="empty">NO ACTIVE NEAR-MISSES — the system has not detected an operational near-miss in the current window.</p>`;
    box.querySelectorAll("[data-open-pattern]").forEach((b) =>
      b.addEventListener("click", () => {
        if (typeof onOpenPattern === "function") {
          onOpenPattern(b.dataset.openPattern);
        }
      })
    );
  } catch (e) {
    box.innerHTML = `<p class="empty">${esc(errMsg(e, "Near-miss data"))}</p>`;
  }
}
