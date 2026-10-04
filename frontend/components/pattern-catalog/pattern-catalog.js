/* Pattern catalog component: catalog of recurring near-miss scenarios */

async function refreshPatterns(onOpenPattern) {
  const box = $("patterns");
  if (!box) return;
  try {
    const patterns = await jget("/patterns?limit=50");
    if (!patterns.length) {
      box.innerHTML = `<p class="empty">No recurring patterns yet — ingestion or detection may still be running.</p>`;
      return;
    }
    box.innerHTML = patterns
      .map(
        (p) => `<article class="card">
      <h3>${esc(p.title)}</h3>
      <p>${esc(p.recurrence_count)} events · severity ${esc(
          p.severity
        )} · confidence ${esc(p.confidence_score)}</p>
      <button type="button" data-pattern="${esc(
        p.id
      )}">Investigate</button></article>`
      )
      .join("");
    box.querySelectorAll("[data-pattern]").forEach((b) =>
      b.addEventListener("click", () => {
        if (typeof onOpenPattern === "function") {
          onOpenPattern(b.dataset.pattern);
        }
      })
    );
  } catch {
    box.innerHTML = `<p class="empty">Patterns unavailable.</p>`;
  }
}
