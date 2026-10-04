/* Sparkline component: lightweight inline SVG progression graphs */
function sparkline(series, label) {
  if (!series || !series.length) return "";
  const max = Math.max(...series.map((p) => p.delay_minutes), 1);
  const pts = series
    .map(
      (p, i) =>
        `${(i / Math.max(series.length - 1, 1)) * 100},${
          30 - (p.delay_minutes / max) * 28
        }`
    )
    .join(" ");
  return `<svg class="spark" viewBox="0 0 100 30" role="img" aria-label="${esc(
    label
  )}"><title>${esc(label)}</title><polyline points="${pts}"/></svg>`;
}
