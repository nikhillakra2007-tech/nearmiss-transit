/* Timeline chart component: detailed SVG delay trajectory with peak/recovery markers */

function occTextSummary(series) {
  if (!series || !series.length) return "Insufficient delay-series data";
  const first = series[0].delay_minutes;
  const peak = Math.max(...series.map((s) => s.delay_minutes));
  const final = series[series.length - 1].delay_minutes;
  return `Delay increased from ${first} minutes to a peak of ${peak} minutes before recovering to ${final} minutes.`;
}

function timelineSVG(series, baselineMin, key) {
  if (!series || !series.length) return "";
  const W = 300,
    H = 120,
    P = 8,
    BW = W - 34,
    BH = H - 30;
  const max = Math.max(...series.map((p) => p.delay_minutes), 1);
  const X = (i) => P + (i / Math.max(series.length - 1, 1)) * BW;
  const Y = (v) => P + BH - (v / max) * BH;
  const pts = series
    .map((p, i) => `${X(i).toFixed(1)},${Y(p.delay_minutes).toFixed(1)}`)
    .join(" ");
  const peakI = series.reduce(
    (bi, p, i) => (p.delay_minutes > series[bi].delay_minutes ? i : bi),
    0
  );
  const lastI = series.length - 1;
  const t0 = (series[0].timestamp || "").slice(11, 16);
  const t1 = (series[lastI].timestamp || "").slice(11, 16);

  let base = "";
  if (baselineMin != null && isFinite(baselineMin)) {
    const y = Y(Math.min(baselineMin, max));
    base = `<line x1="${P}" y1="${y}" x2="${P + BW}" y2="${y}" stroke="#d29922" stroke-dasharray="4 3" stroke-width="1.5"/><text x="${
      P + BW
    }" y="${y - 3}" font-size="8" fill="#d29922" text-anchor="end">baseline ${baselineMin} min</text>`;
  }
  const label = `Delay timeline: ${occTextSummary(series)}`;
  return `<svg class="tl" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="tlt-${key}"><title id="tlt-${key}">${esc(
    label
  )}</title>
    <line x1="${P}" y1="${P}" x2="${P}" y2="${P + BH}" stroke="#30363d"/><line x1="${P}" y1="${P + BH}" x2="${P + BW}" y2="${P + BH}" stroke="#30363d"/>
    <text x="2" y="${Y(max) + 3}" font-size="8" fill="#9aa4b2">${max}</text><text x="2" y="${P + BH}" font-size="8" fill="#9aa4b2">0</text><text x="2" y="${
      (P + P + BH) / 2 + 3
    }" font-size="8" fill="#9aa4b2">min</text>
    <text x="${P}" y="${H - 4}" font-size="8" fill="#9aa4b2">${esc(t0)}</text><text x="${
      P + BW
    }" y="${H - 4}" font-size="8" fill="#9aa4b2" text-anchor="end">${esc(t1)}</text>
    ${base}<polyline points="${pts}" fill="none" stroke="#58a6ff" stroke-width="2"/>
    <circle cx="${X(peakI)}" cy="${Y(series[peakI].delay_minutes)}" r="4" fill="#c54b38" stroke="#fff" stroke-width="1.5"/><text x="${X(
      peakI
    )}" y="${Math.max(Y(series[peakI].delay_minutes) - 8, 12)}" font-size="9" font-weight="700" fill="#a83522" text-anchor="middle" paint-order="stroke" stroke="#fffefa" stroke-width="3" stroke-linejoin="round">Peak ${
      series[peakI].delay_minutes
    }m</text>
    <circle cx="${X(lastI)}" cy="${Y(series[lastI].delay_minutes)}" r="3.5" fill="#25674c" stroke="#fff" stroke-width="1.5"/><text x="${X(
      lastI
    )}" y="${Math.min(Y(series[lastI].delay_minutes) + 14, H - 6)}" font-size="8.5" font-weight="600" fill="#25674c" text-anchor="end" paint-order="stroke" stroke="#fffefa" stroke-width="3" stroke-linejoin="round">Final ${
      series[lastI].delay_minutes
    }m</text></svg>`;
}
