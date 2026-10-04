/* Forecast monitor component: emerging early-warning operational signals */

async function refreshForecast(onOpenPattern) {
  const box = $("forecast");
  if (!box) return;
  try {
    const patterns = await jget("/patterns?limit=10");
    const forecastResults = await Promise.all(
      patterns.map((p) => jget(`/patterns/${p.id}/forecast`).catch(() => null))
    );
    const cards = [];
    patterns.forEach((p, idx) => {
      const f = forecastResults[idx];
      if (!f || f.status === "INSUFFICIENT_DATA" || f.score == null) return;
      const sigs = (f.signals || [])
        .filter((s) => s.available)
        .map(
          (s) =>
            `<li>+${esc(s.contribution)} ${esc(s.summary)} <em>(${
              (s.evidence_ids || []).length
            } evidence)</em></li>`
        )
        .join("");
      cards.push(`<article class="card"><h3>${esc(p.title)}</h3>
        <p><strong>${esc(f.score)} / 100</strong> · <span class="sev ${
        f.status === "EMERGING" ? "HIGH" : "MEDIUM"
      }">${esc(f.status)}</span></p>
        <details class="evdet"><summary>Why is this emerging?</summary><div>
          <ul class="evtl">${sigs}</ul>
          <p class="fineprint">Evaluated ${esc(
            f.evaluated_at
          )}. This is an operational early-warning signal, not a guaranteed prediction.</p></div></details>
        <button type="button" data-open-pattern="${esc(
          p.id
        )}">View pattern</button></article>`);
    });
    box.innerHTML = cards.length
      ? cards.join("")
      : `<p class="empty">No emerging signals — no pattern currently resembles historical near-miss conditions strongly enough.</p>`;
    box.querySelectorAll("[data-open-pattern]").forEach((b) =>
      b.addEventListener("click", () => {
        if (typeof onOpenPattern === "function") {
          onOpenPattern(b.dataset.openPattern);
        }
      })
    );
  } catch (e) {
    box.innerHTML = `<p class="empty">${esc(errMsg(e, "Forecast data"))}</p>`;
  }
}
