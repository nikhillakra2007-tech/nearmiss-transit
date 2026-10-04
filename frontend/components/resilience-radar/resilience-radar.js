/* Operational resilience radar component: composite stress indicators per corridor */

async function refreshResilience(onOpenPattern) {
  const box = $("resilience");
  if (!box) return;
  try {
    const [data, patterns] = await Promise.all([
      jget("/resilience?limit=20"),
      jget("/patterns?limit=100"),
    ]);
    const patByRoute = {};
    patterns.forEach((p) => {
      if (p.route_id && !patByRoute[p.route_id]) patByRoute[p.route_id] = p.id;
    });
    const items = (data.items || []).filter(
      (it) => it.status !== "INSUFFICIENT_DATA"
    );
    if (!items.length) {
      box.innerHTML = `<p class="empty">INSUFFICIENT DATA — no route has enough observed history for a resilience indicator.</p>`;
      return;
    }
    box.innerHTML = items
      .map((it) => {
        const bars = Object.entries(it.signals || {})
          .filter(([, v]) => v != null)
          .map(
            ([k, v]) =>
              `<p>${esc(k)}: ${esc(v)}<span class="sigbar" role="img" aria-label="${esc(
                k
              )} stress ${esc(v)} of 100"><i style="width:${esc(
                Math.min(v, 100)
              )}%"></i></span></p>`
          )
          .join("");
        const pid = patByRoute[it.route_id];
        return `<article class="card"><h3>Route ${esc(it.route)}</h3>
        <p><strong>${esc(it.resilience)} / 100</strong> · ${esc(it.status)} (${esc(
          it.samples ? it.samples.near_misses : 0
        )} near-misses)</p>
        ${bars}${
          pid
            ? `<button type="button" data-open-pattern="${esc(
                pid
              )}">View pattern</button>`
            : ""
        }</article>`;
      })
      .join("");
    box.querySelectorAll("[data-open-pattern]").forEach((b) =>
      b.addEventListener("click", () => {
        if (typeof onOpenPattern === "function") {
          onOpenPattern(b.dataset.openPattern);
        }
      })
    );
  } catch (e) {
    box.innerHTML = `<p class="empty">${esc(errMsg(e, "Resilience data"))}</p>`;
  }
}
