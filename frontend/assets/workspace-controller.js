/* NearMiss Transit dashboard — renders /api/v1 only; no business logic duplicated. */
const $ = (id) => document.getElementById(id);
const API = "/api/v1";
let MODE = "LIVE";

async function jget(path) {
  const r = await fetch(API + path);
  if (!r.ok) { const e = new Error(`${r.status} on ${path}`); e.status = r.status; throw e; }
  return r.json();
}

async function jpost(path, body) {
  const r = await fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) { const e = new Error(`${r.status} on ${path}`); e.status = r.status; try { e.detail = await r.json(); } catch { /* ignore */ } return Promise.reject(e); }
  return r.json();
}

function errMsg(e, what) {
  const s = e && e.status;
  if (s === 404) return `${what}: not found.`;
  if (s === 422) return `${what}: invalid request was rejected.`;
  if (s >= 500) return `${what}: server error.`;
  return `${what} unavailable.`;
}

function esc(s) { return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

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
    $("feed-state").textContent = "Feed: " + (h.feed === "FEED_UNAVAILABLE" ? "unavailable (replay OK)" : h.feed);
    if (!$("last-update").textContent || $("last-update").textContent === "Last update: —") {
      $("last-update").textContent = "Last update: " + new Date().toLocaleTimeString();
    }
  } catch { $("feed-state").textContent = "Feed: backend unreachable"; }
}

async function refreshOps() {
  try {
    const [events, vehicles, routes] = await Promise.all([
      jget("/events?limit=5"), jget("/vehicles?limit=100"), jget("/routes?limit=100")]);
    $("ops").innerHTML = `<table><tr><th scope="col">Routes</th><th scope="col">Vehicles</th><th scope="col">Recent events</th></tr>
      <tr><td>${routes.length}</td><td>${vehicles.length}</td><td>${events.length} shown</td></tr></table>
      <table><tr><th scope="col">Observed at</th><th scope="col">Type</th><th scope="col">Delay (s)</th></tr>
      ${events.map((e) => {
        const d = e.delay_seconds != null ? `${e.delay_seconds}s` : (e.raw_payload && e.raw_payload.delay_seconds != null ? `${e.raw_payload.delay_seconds}s` : (e.raw_payload && e.raw_payload.delay != null ? `${e.raw_payload.delay}s` : "Normal (0s)"));
        return `<tr><td>${esc(e.observed_at)}</td><td>${esc(e.event_type)}</td><td><strong>${esc(d)}</strong></td></tr>`;
      }).join("")}</table>`;
    const latest = events.map((e) => e.observed_at).filter(Boolean).sort().pop();
    if (latest) {
      const isoStr = latest.endsWith("Z") || latest.includes("+") ? latest : latest + "Z";
      const diffMs = Date.now() - new Date(isoStr).getTime();
      const mins = Math.max(0, Math.round(diffMs / 60000));
      $("freshness").textContent = mins < 2 ? "Data freshness: just now" : `Data freshness: ${mins} min ago`;
    }
  } catch { $("ops").innerHTML = `<p class="empty">Operations unavailable.</p>`; }
}

function sparkline(series, label) {
  if (!series.length) return "";
  const max = Math.max(...series.map((p) => p.delay_minutes), 1);
  const pts = series.map((p, i) => `${(i / Math.max(series.length - 1, 1)) * 100},${30 - (p.delay_minutes / max) * 28}`).join(" ");
  return `<svg class="spark" viewBox="0 0 100 30" role="img" aria-label="${esc(label)}"><title>${esc(label)}</title><polyline points="${pts}"/></svg>`;
}

async function refreshResilience() {
  const box = $("resilience");
  try {
    const [data, patterns] = await Promise.all([jget("/resilience?limit=20"), jget("/patterns?limit=100")]);
    const patByRoute = {};
    patterns.forEach((p) => { if (p.route_id && !patByRoute[p.route_id]) patByRoute[p.route_id] = p.id; });
    const items = (data.items || []).filter((it) => it.status !== "INSUFFICIENT_DATA");
    if (!items.length) { box.innerHTML = `<p class="empty">INSUFFICIENT DATA — no route has enough observed history for a resilience indicator.</p>`; return; }
    box.innerHTML = items.map((it) => {
      const bars = Object.entries(it.signals || {}).filter(([, v]) => v != null).map(([k, v]) =>
        `<p>${esc(k)}: ${esc(v)}<span class="sigbar" role="img" aria-label="${esc(k)} stress ${esc(v)} of 100"><i style="width:${esc(Math.min(v, 100))}%"></i></span></p>`).join("");
      const pid = patByRoute[it.route_id];
      return `<article class="card"><h3>Route ${esc(it.route)}</h3>
        <p><strong>${esc(it.resilience)} / 100</strong> · ${esc(it.status)} (${esc(it.samples ? it.samples.near_misses : 0)} near-misses)</p>
        ${bars}${pid ? `<button type="button" data-open-pattern="${esc(pid)}">View pattern</button>` : ""}</article>`;
    }).join("");
    box.querySelectorAll("[data-open-pattern]").forEach((b) => b.addEventListener("click", () => {
      openPattern(b.dataset.openPattern);
      $("h-detail").focus({ preventScroll: true });
      $("h-detail").scrollIntoView();
    }));
  } catch (e) { box.innerHTML = `<p class="empty">${esc(errMsg(e, "Resilience data"))}</p>`; }
}

async function refreshForecast() {
  const box = $("forecast");
  try {
    const patterns = await jget("/patterns?limit=10");
    const forecastResults = await Promise.all(
      patterns.map(p => jget(`/patterns/${p.id}/forecast`).catch(() => null))
    );
    const cards = [];
    patterns.forEach((p, idx) => {
      const f = forecastResults[idx];
      if (!f || f.status === "INSUFFICIENT_DATA" || f.score == null) return;
      const sigs = (f.signals || []).filter((s) => s.available).map((s) =>
        `<li>+${esc(s.contribution)} ${esc(s.summary)} <em>(${(s.evidence_ids || []).length} evidence)</em></li>`).join("");
      cards.push(`<article class="card"><h3>${esc(p.title)}</h3>
        <p><strong>${esc(f.score)} / 100</strong> · <span class="sev ${f.status === "EMERGING" ? "HIGH" : "MEDIUM"}">${esc(f.status)}</span></p>
        <details class="evdet"><summary>Why is this emerging?</summary><div>
          <ul class="evtl">${sigs}</ul>
          <p class="fineprint">Evaluated ${esc(f.evaluated_at)}. This is an operational early-warning signal, not a guaranteed prediction.</p></div></details>
        <button type="button" data-open-pattern="${esc(p.id)}">View pattern</button></article>`);
    });
    box.innerHTML = cards.length ? cards.join("")
      : `<p class="empty">No emerging signals — no pattern currently resembles historical near-miss conditions strongly enough.</p>`;
    box.querySelectorAll("[data-open-pattern]").forEach((b) => b.addEventListener("click", () => {
      openPattern(b.dataset.openPattern);
      $("h-detail").focus({ preventScroll: true });
      $("h-detail").scrollIntoView();
    }));
  } catch (e) { box.innerHTML = `<p class="empty">${esc(errMsg(e, "Forecast data"))}</p>`; }
}

async function refreshNearMisses() {
  const box = $("nearmisses");
  try {
    const [patterns, routes] = await Promise.all([jget("/patterns?limit=20"), jget("/routes?limit=200")]);
    const routeName = {};
    routes.forEach((r) => { routeName[r.id] = r.short_name || r.long_name || r.external_route_id || "unknown route"; });
    const targetPatterns = patterns.slice(0, 10);
    const details = await Promise.all(
      targetPatterns.map(p => jget(`/patterns/${p.id}/detail`).catch(() => null))
    );
    const cards = [];
    const seenRoutes = new Set();
    targetPatterns.forEach((p, idx) => {
      const det = details[idx];
      if (!det || !det.members || !det.members.length) return;
      const members = [...det.members].sort((a, b) => new Date(b.detected_at || 0) - new Date(a.detected_at || 0));
      for (const m of members) {
        const routeKey = m.route_id || p.route_id || p.id;
        if (seenRoutes.has(routeKey)) continue;
        seenRoutes.add(routeKey);

        const series = Array.isArray(m.delay_series) ? m.delay_series : [];
        const peak = series.length ? Math.max(...series.map((s) => s.delay_minutes))
          : (m.abnormal_value || {}).peak_delay != null ? Math.round((m.abnormal_value.peak_delay / 60) * 10) / 10 : null;
        const final = series.length ? series[series.length - 1].delay_minutes
          : (m.abnormal_value || {}).final_delay != null ? Math.round((m.abnormal_value.final_delay / 60) * 10) / 10 : null;
        const prog = series.length
          ? series.map((s) => s.delay_minutes).join(" → ") + " min"
          : "Insufficient delay-series data";
        const recovered = m.recovery_event_id
          ? `Recovered: yes${m.recovery_duration_seconds != null ? ` (${m.recovery_duration_seconds}s)` : ""}`
          : "Recovered: not recorded";
        cards.push(`<article class="card">
          <h3>${esc(routeName[m.route_id] || m.route_id || "Unknown route")}</h3>
          <p><span class="sev ${esc(m.severity)}">${esc(m.severity)}</span> ${esc(m.near_miss_type)}</p>
          <p class="prog">${esc(prog)}</p>
          ${sparkline(series, `Delay progression, peak ${peak} minutes, final ${final} minutes`)}
          <p>Peak ${esc(peak)} min → final ${esc(final)} min · ${esc(recovered)}</p>
          <p>Recurring: part of “${esc(p.title)}” · ${esc(p.recurrence_count)} occurrences · ${esc(m.detected_at)}</p>
          <button type="button" data-open-pattern="${esc(p.id)}">Open investigation</button></article>`);
      }
    });
    box.innerHTML = cards.length ? cards.join("")
      : `<p class="empty">NO ACTIVE NEAR-MISSES — the system has not detected an operational near-miss in the current window.</p>`;
    box.querySelectorAll("[data-open-pattern]").forEach((b) => b.addEventListener("click", () => {
      openPattern(b.dataset.openPattern);
      const h = $("h-detail");
      h.focus({ preventScroll: true });
      h.scrollIntoView();
    }));
  } catch (e) { box.innerHTML = `<p class="empty">${esc(errMsg(e, "Near-miss data"))}</p>`; }
}

const OUTCOME_MARK = { IMPROVED: "✓", NO_SIGNIFICANT_CHANGE: "▬", WORSENED: "⚠", INSUFFICIENT_DATA: "?" };

function verifySVG(v, key) {
  const b = v.baseline_metrics || {}, a = v.post_metrics || {};
  if (b.avg_delay == null || a.avg_delay == null) return "";
  const max = Math.max(b.avg_delay, a.avg_delay, 1);
  const wb = Math.max((b.avg_delay / max) * 100, 2), wa = Math.max((a.avg_delay / max) * 100, 2);
  const label = `Verification: before ${b.avg_delay} seconds average delay, after ${a.avg_delay} seconds. Outcome ${v.outcome}.`;
  return `<svg class="vbars" viewBox="0 0 300 64" role="img" aria-labelledby="vb-${key}"><title id="vb-${key}">${esc(label)}</title>
    <text x="0" y="14" font-size="10" fill="#e6edf3">BEFORE ${esc(b.avg_delay)}s (n=${esc(b.n)}, near-misses ${esc(b.near_misses)})</text>
    <rect x="0" y="18" width="${wb * 2.6}" height="12" fill="#58a6ff"/>
    <text x="0" y="48" font-size="10" fill="#e6edf3">AFTER ${esc(a.avg_delay)}s (n=${esc(a.n)}, near-misses ${esc(a.near_misses)})</text>
    <rect x="0" y="52" width="${wa * 2.6}" height="12" fill="#3fb950"/></svg>`;
}

async function resolveEvidence(e) {
  const base = `<p><strong>${esc(e.evidence_type)}</strong> · observed ${esc(fmtT(e.observed_at))} · confidence ${esc(e.confidence_score)}</p><p>${esc(e.description)}</p><p>Source: ${esc(e.source_entity_type)} ${esc(shortId(e.source_entity_id))}</p>`;
  try {
    if (e.source_entity_type === "transit_event") {
      const ev = await jget(`/events/${e.source_entity_id}`);
      return `${base}<p>Linked event: ${esc(ev.event_type)} at ${esc(fmtT(ev.observed_at))}, delay ${esc(ev.delay_seconds)}s.</p>`;
    }
    if (e.source_entity_type === "near_miss") {
      const nm = await jget(`/near-misses/${e.source_entity_id}`);
      const ab = nm.abnormal_value || {};
      return `${base}<p>Linked near-miss: ${esc(nm.near_miss_type)}, peak ${esc(ab.peak_delay != null ? Math.round(ab.peak_delay / 60 * 10) / 10 + " min" : "—")}, status ${esc(nm.status)}.</p>`;
    }
    return `${base}<p>Full ${esc(e.source_entity_type)} record is not exposed by the API — showing stored evidence fields only.</p>`;
  } catch { return `${base}<p class="empty">Evidence details unavailable.</p>`; }
}

function evidenceItem(e) {
  return `<details class="evdet" data-evidence="${esc(e.id)}"><summary><span class="claimtag FACT">FACT</span> [${esc(shortId(e.id))}] ${esc(e.evidence_type)} — ${esc(e.description)}</summary><div class="evbody"><p class="empty">Select to load source details…</p></div></details>`;
}

function renderVerification(v, key) {
  const mark = OUTCOME_MARK[v.outcome] || "?";
  return `<div class="verify"><p><strong>${esc(mark)} ${esc(v.outcome)}</strong> (backend-authoritative)</p>
    ${verifySVG(v, key)}
    <p>Window: ${esc(fmtT(v.verification_started_at))} → ${esc(fmtT(v.verification_ended_at))}</p>
    <p>${esc(v.explanation)}</p></div>`;
}

function renderIntervention(x, rec, patId) {
  const exec = x.execution_status === "EXECUTED"
    ? "✓ Executed (backend-confirmed)"
    : `${x.execution_status} — recommendation prepared for external operator handoff.`;
  const vs = (x.verifications || []).map((v, i) => renderVerification(v, `${x.id}-${i}`)).join("") || `<p class="empty">Not enough post-intervention data yet.</p>`;
  return `<div class="iv"><p>Intervention: ${esc(x.intervention_type)} → <strong>${esc(exec)}</strong></p><p>Target: ${esc(x.target)}</p>${vs}</div>`;
}

function interventionForm(rec, patId) {
  return `<form class="ivform" data-ivform="${esc(rec.id)}" data-pattern="${esc(patId)}">
    <h5>Record intervention handoff</h5>
    <label>Action type <select name="intervention_type">
      <option>OPERATIONAL_REVIEW</option><option>OBSERVATION_TASK</option>
      <option>SCHEDULE_REVIEW_REQUEST</option><option>ALERT_FOLLOWUP</option></select></label>
    <label>Target <input name="target" maxlength="200" required placeholder="e.g. affected route and time window"></label>
    <button type="submit">Record intervention</button>
    <span class="formmsg" role="status"></span></form>`;
}

async function refreshPatterns() {  try {
    const patterns = await jget("/patterns?limit=50");
    if (!patterns.length) { $("patterns").innerHTML = `<p class="empty">No recurring patterns yet — ingestion or detection may still be running.</p>`; return; }
    $("patterns").innerHTML = patterns.map((p) => `<article class="card">
      <h3>${esc(p.title)}</h3>
      <p>${esc(p.recurrence_count)} events · severity ${esc(p.severity)} · confidence ${esc(p.confidence_score)}</p>
      <button type="button" data-pattern="${esc(p.id)}">Investigate</button></article>`).join("");
    document.querySelectorAll("[data-pattern]").forEach((b) => b.addEventListener("click", () => openPattern(b.dataset.pattern)));
  } catch { $("patterns").innerHTML = `<p class="empty">Patterns unavailable.</p>`; }
}

let ROUTE_NAMES = {};
async function ensureRouteNames() {
  if (Object.keys(ROUTE_NAMES).length) return;
  try {
    const r = await jget("/routes?limit=200");
    r.forEach((x) => { ROUTE_NAMES[x.id] = x.short_name || x.long_name || x.external_route_id; });
  } catch { /* names stay raw IDs */ }
}
function routeLabel(id) { return ROUTE_NAMES[id] || id || "Unknown route"; }
function fmtT(iso) { try { return new Date(iso).toLocaleString(); } catch { return String(iso); } }
function shortId(id) { return String(id || "").slice(0, 8); }

function occTextSummary(series) {
  if (!series.length) return "Insufficient delay-series data";
  const first = series[0].delay_minutes;
  const peak = Math.max(...series.map((s) => s.delay_minutes));
  const final = series[series.length - 1].delay_minutes;
  return `Delay increased from ${first} minutes to a peak of ${peak} minutes before recovering to ${final} minutes.`;
}

function timelineSVG(series, baselineMin, key) {
  if (!series.length) return "";
  const W = 300, H = 120, P = 8, BW = W - 34, BH = H - 30;
  const max = Math.max(...series.map((p) => p.delay_minutes), 1);
  const X = (i) => P + (i / Math.max(series.length - 1, 1)) * BW;
  const Y = (v) => P + BH - (v / max) * BH;
  const pts = series.map((p, i) => `${X(i).toFixed(1)},${Y(p.delay_minutes).toFixed(1)}`).join(" ");
  const peakI = series.reduce((bi, p, i) => (p.delay_minutes > series[bi].delay_minutes ? i : bi), 0);
  const lastI = series.length - 1;
  const t0 = (series[0].timestamp || "").slice(11, 16), t1 = (series[lastI].timestamp || "").slice(11, 16);
  let base = "";
  if (baselineMin != null && isFinite(baselineMin)) {
    const y = Y(Math.min(baselineMin, max));
    base = `<line x1="${P}" y1="${y}" x2="${P + BW}" y2="${y}" stroke="#d29922" stroke-dasharray="4 3" stroke-width="1.5"/><text x="${P + BW}" y="${y - 3}" font-size="8" fill="#d29922" text-anchor="end">baseline ${baselineMin} min</text>`;
  }
  const label = `Delay timeline: ${occTextSummary(series)}`;
  return `<svg class="tl" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="tlt-${key}"><title id="tlt-${key}">${esc(label)}</title>
    <line x1="${P}" y1="${P}" x2="${P}" y2="${P + BH}" stroke="#30363d"/><line x1="${P}" y1="${P + BH}" x2="${P + BW}" y2="${P + BH}" stroke="#30363d"/>
    <text x="2" y="${Y(max) + 3}" font-size="8" fill="#9aa4b2">${max}</text><text x="2" y="${P + BH}" font-size="8" fill="#9aa4b2">0</text><text x="2" y="${(P + P + BH) / 2 + 3}" font-size="8" fill="#9aa4b2">min</text>
    <text x="${P}" y="${H - 4}" font-size="8" fill="#9aa4b2">${esc(t0)}</text><text x="${P + BW}" y="${H - 4}" font-size="8" fill="#9aa4b2" text-anchor="end">${esc(t1)}</text>
    ${base}<polyline points="${pts}" fill="none" stroke="#58a6ff" stroke-width="2"/>
    <circle cx="${X(peakI)}" cy="${Y(series[peakI].delay_minutes)}" r="4" fill="#c54b38" stroke="#fff" stroke-width="1.5"/><text x="${X(peakI)}" y="${Math.max(Y(series[peakI].delay_minutes) - 8, 12)}" font-size="9" font-weight="700" fill="#a83522" text-anchor="middle" paint-order="stroke" stroke="#fffefa" stroke-width="3" stroke-linejoin="round">Peak ${series[peakI].delay_minutes}m</text>
    <circle cx="${X(lastI)}" cy="${Y(series[lastI].delay_minutes)}" r="3.5" fill="#25674c" stroke="#fff" stroke-width="1.5"/><text x="${X(lastI)}" y="${Math.min(Y(series[lastI].delay_minutes) + 14, H - 6)}" font-size="8.5" font-weight="600" fill="#25674c" text-anchor="end" paint-order="stroke" stroke="#fffefa" stroke-width="3" stroke-linejoin="round">Final ${series[lastI].delay_minutes}m</text></svg>`;
}

function chainCard(c, evMap, patId) {
  const wins = c.pairs.map((p) => `<li>${esc(fmtT(p.a_at))} → ${esc(fmtT(p.b_at))} (gap ${esc(p.gap_minutes)} min)</li>`).join("");
  const evs = (c.evidence_ids || []).map((id) => evMap[id] ? evidenceItem(evMap[id]) : "").join("")
    || `<p class="empty">Evidence details unavailable.</p>`;
  return `<article class="card chain" aria-label="Operational chain, ${esc(c.strength)}">
    <h4>OPERATIONAL CHAIN — <span class="sev ${c.strength === "STRONG_RECURRING" ? "HIGH" : "MEDIUM"}">${esc(c.strength)}</span></h4>
    <p><strong>${esc(routeLabel(c.source_route_id))}</strong> (${esc(c.source_type)})</p>
    <p aria-hidden="true">↓</p><p><strong>${esc(c.relationship)}</strong> (recurring sequence — temporal association, not causal proof)</p><p aria-hidden="true">↓</p>
    <p><strong>${esc(routeLabel(c.target_route_id))}</strong> (${esc(c.target_type)})</p>
    <p>Observed in ${esc(c.occurrences)} windows · average gap ${esc(c.avg_gap_minutes)} min · ${(c.evidence_ids || []).length} supporting evidence items</p>
    <details class="evdet"><summary>Why is this connected?</summary><div>
      <p>Each window shows the source near-miss starting before the target near-miss. Relationship: RECURRING TEMPORAL ASSOCIATION. Temporal association, not proof of causation.</p>
      <ol class="evtl">${wins}</ol><h5>Supporting evidence (select to trace)</h5>${evs}</div></details>
    <button type="button" data-investigate-chain="${esc(c.key)}">Investigate chain</button>
    <div class="chainresult" data-chainresult="${esc(c.key)}"></div>
    <form class="ivform" data-chaincompare="${esc(c.key)}">
      <h5>Compare occurrence counts across windows (counts only — no outcome inferred)</h5>
      <label>Since <input type="datetime-local" name="since"></label>
      <label>Until <input type="datetime-local" name="until"></label>
      <button type="submit">Compare windows</button>
      <span class="formmsg" role="status"></span></form></article>`;
}

function fingerprintChips(fp) {
  const chips = [fp.route, fp.time_bucket, fp.type, fp.peak_bucket + " PEAK",
    fp.recovery_bucket + " RECOVERY", fp.recurrence_strength,
    fp.chain_exposure ? "CHAIN EXPOSURE" : "NO CHAIN"];
  return `<div class="chips" role="img" aria-label="Operational fingerprint: ${esc(chips.join(", "))}">${chips.map((c) => `<span class="chip">${esc(c)}</span>`).join("")}</div>
    <p class="fineprint">Signature <code>${esc(fp.canonical_id)}</code> — operational signature, not a root-cause claim.</p>`;
}

function renderReplayPointDetail(rp, idx) {
  const p = rp.timeline[idx];
  if (!p) return `<p class="empty">Select a timeline point.</p>`;
  const sigs = (p.signals || []).filter((s) => s.available).map((s) =>
    `<li>+${esc(s.contribution)} ${esc(s.summary)}</li>`).join("")
    || `<li>No evidence-supported signals available at this cutoff.</li>`;
  return `<p><strong>${esc(p.score == null ? "insufficient data" : p.score + " / 100")}</strong> · ${esc(p.band)}</p>
    <p>Cutoff ${esc(fmtT(p.cutoff))} · ${esc(p.minutes_before_target)} minutes before target · ${esc(p.signals_available)} of ${esc(p.signals_total)} signals available</p>
    <ul class="evtl">${sigs}</ul>`;
}

function renderReplay(rp) {
  const dis = `<p class="fineprint">${esc(rp.disclaimer || "Historical replay using observed data.")}</p>`;
  if (!rp || rp.status === "INSUFFICIENT_DATA" || !(rp.timeline || []).length) {
    return `<p class="empty">Insufficient history for a historical replay — no scored cutoff in the replay window.</p>${dis}`;
  }
  const fw = rp.first_watch
    ? `First WATCH: ${esc(rp.first_watch.minutes_before_target)} minutes before near-miss`
    : `No WATCH threshold crossing in the replay window.`;
  const fe = rp.first_emerging
    ? `First EMERGING: ${esc(rp.first_emerging.minutes_before_target)} minutes before near-miss`
    : `No EMERGING threshold crossing in the replay window.`;
  const items = rp.timeline.map((p, i) => {
    const isTarget = i === rp.timeline.length - 1;
    const marks = [
      rp.first_watch && p.cutoff === rp.first_watch.cutoff ? "FIRST WATCH" : "",
      rp.first_emerging && p.cutoff === rp.first_emerging.cutoff ? "FIRST EMERGING" : "",
      isTarget ? "TARGET NEAR-MISS" : "",
    ].filter(Boolean).map((m) => ` <strong>${esc(m)}</strong>`).join("");
    return `<li>${esc(p.minutes_before_target)} min before — ${esc(p.band)} — ${esc(p.score == null ? "insufficient data" : p.score)}${marks}</li>`;
  }).join("");
  const rows = rp.timeline.map((p) =>
    `<tr><td>${esc(fmtT(p.cutoff))}</td><td>${esc(p.minutes_before_target)}</td><td>${esc(p.score == null ? "—" : p.score)}</td><td>${esc(p.band)}</td></tr>`).join("");
  const opts = rp.timeline.map((p, i) =>
    `<option value="${i}">${esc(p.minutes_before_target)} min before — ${esc(p.band)}${p.score == null ? "" : " " + esc(p.score)}</option>`).join("");
  return `<p><strong>${esc(fw)}</strong></p><p><strong>${esc(fe)}</strong></p>
    <p class="fineprint">Target recorded near-miss: ${esc(fmtT(rp.target_timestamp))} · lookback ${esc(rp.lookback_minutes)} min · step ${esc(rp.step_minutes)} min · ${esc(rp.timeline.length)} cutoffs</p>
    <ol class="ewtl" aria-label="Early-warning replay timeline">${items}</ol>
    <table><caption>Early-warning replay timeline (text alternative)</caption>
      <tr><th scope="col">Cutoff</th><th scope="col">Minutes before</th><th scope="col">Score</th><th scope="col">Band</th></tr>${rows}</table>
    <label>Timeline point <select data-rpselect>${opts}</select></label>
    <div data-rpdetail>${renderReplayPointDetail(rp, rp.timeline.length - 1)}</div>${dis}`;
}

async function openPattern(id) {
  const d = $("detail");
  d.innerHTML = `<p class="empty">Loading pattern evidence…</p>`;
  try {
    await ensureRouteNames();
    const det = await jget(`/patterns/${id}/detail`);
    const getOccTime = (m) => {
      const s = Array.isArray(m.delay_series) ? m.delay_series : [];
      return (s.length && s[s.length - 1].timestamp) ? s[s.length - 1].timestamp : m.detected_at;
    };
    const members = (det.members || []).slice().sort((a, b) => new Date(getOccTime(a)) - new Date(getOccTime(b)));
    if (!members.length) { d.innerHTML = `<p class="empty">No near-miss occurrences are available for this pattern.</p>`; return; }
    const hours = members.map((m) => new Date(getOccTime(m)).getHours()).filter((h) => !isNaN(h));
    const window = hours.length ? `Typical window: ${String(Math.min(...hours)).padStart(2, "0")}:00–${String(Math.max(...hours) + 1).padStart(2, "0")}:00 (derived from ${hours.length} occurrence timestamps)` : "Time window: not available";
    const route = routeLabel((members[0] || {}).route_id);
    const invStatus = (det.investigations || []).map((i) => i.status).join(", ") || "no investigation yet";
    let usableSeries = 0;
    const occs = members.map((m, n) => {
      const series = Array.isArray(m.delay_series) ? m.delay_series : [];
      if (series.length) usableSeries++;
      const occTime = (series.length && series[series.length - 1].timestamp) || m.detected_at;
      const baseMin = m.baseline_value && m.baseline_value.median != null
        ? Math.round((m.baseline_value.median / 60) * 10) / 10 : null;
      const peak = series.length ? Math.max(...series.map((s) => s.delay_minutes)) : null;
      const final = series.length ? series[series.length - 1].delay_minutes : null;
      const ev = [];
      if (series.length) {
        ev.push(`<li>Series start ${esc(fmtT(series[0].timestamp))} — delay ${esc(series[0].delay_minutes)} min (observed point)</li>`);
        const pk = series.reduce((bi, p, i) => (p.delay_minutes > series[bi].delay_minutes ? i : bi), 0);
        ev.push(`<li>Peak ${esc(fmtT(series[pk].timestamp))} — ${esc(series[pk].delay_minutes)} min (observed series maximum)</li>`);
        ev.push(`<li>Final ${esc(fmtT(series[series.length - 1].timestamp))} — ${esc(series[series.length - 1].delay_minutes)} min (observed point)</li>`);
      }
      if (m.start_event_id) ev.push(`<li>Deviation window opened (event ${esc(shortId(m.start_event_id))})</li>`);
      if (m.recovery_event_id) ev.push(`<li>Recovery recorded${m.recovery_duration_seconds != null ? ` after ${esc(m.recovery_duration_seconds)}s` : ""} (event ${esc(shortId(m.recovery_event_id))})</li>`);
      return `<article class="card occ" aria-label="Occurrence ${n + 1}">
        <h4>Occurrence ${n + 1} — ${esc(fmtT(occTime))}</h4>
        <p>${esc(route)} · ${esc(m.near_miss_type)} · <span class="sev ${esc(m.severity)}">${esc(m.severity)}</span></p>
        ${series.length
          ? `${timelineSVG(series, baseMin, `${pat.id}-${n}`)}<p>${esc(occTextSummary(series))}</p>
             ${baseMin != null ? `<p>Baseline median ${esc(baseMin)} min vs observed peak ${esc(peak)} min.</p>` : `<p>Baseline comparison unavailable for this occurrence — showing verified observed values only.</p>`}`
          : `<p class="empty">Insufficient delay-series data</p>`}
        <ol class="evtl">${ev.join("") || `<li>No source events recorded.</li>`}</ol></article>`;
    }).join("");
    const timelineNote = usableSeries ? "" : `<p class="empty">Insufficient data to construct the full delay timeline.</p>`;
    let chainsHTML = "";
    try {
      const ch = await jget(`/patterns/${id}/chains`);
      const evMap = {};
      (det.investigations || []).forEach((inv) => (inv.evidence || []).forEach((e) => { evMap[e.id] = e; }));
      chainsHTML = `<h4>Operational chains — recurring relationships between near-misses</h4>` +
        ((ch.chains || []).map((c) => chainCard(c, evMap, id)).join("") || `<p class="empty">No recurring operational chains from this pattern's occurrences.</p>`);
      try {
        const mh = await jget(`/patterns/${id}/multihop`);
        chainsHTML += ((mh.chains || []).map((m) => {
          const nodes = m.route_sequence.map((r, i) => {
            const gap = i < m.avg_gaps.length ? `<p aria-hidden="true">↓ ${esc(m.avg_gaps[i])}m</p><p><strong>MAY_CONTRIBUTE_TO</strong> (recurring temporal sequence)</p><p aria-hidden="true">↓</p>` : "";
            return `<p><strong>${esc(routeLabel(r))}</strong></p>${gap}`;
          }).join("");
          const evs = (m.evidence_ids || []).map((eid) => evMap[eid] ? evidenceItem(evMap[eid]) : "").join("")
            || `<p class="empty">Evidence details unavailable.</p>`;
          return `<article class="card chain" aria-label="Multi-hop operational domino, ${esc(m.strength)}">
            <h4>OPERATIONAL DOMINO — <span class="sev ${m.strength === "STRONG_RECURRING" ? "HIGH" : "MEDIUM"}">${esc(m.strength)}</span></h4>
            ${nodes}
            <p>Recurring sequence in ${esc(m.occurrences)} windows · depth ${esc(m.depth)} · ${(m.evidence_ids || []).length} supporting evidence items</p>
            <p class="fineprint">Shows recurring temporal sequences, not proven causation.</p>
            <details class="evdet"><summary>Why is this connected?</summary><div>
              <p>Each window shows the ordered near-miss starts with consistent gaps. Relationship: RECURRING TEMPORAL ASSOCIATION. Temporal association, not proof of causation.</p>
              ${evs}</div></details></article>`;
        }).join(""));
      } catch { chainsHTML += `<p class="empty">Multi-hop data unavailable.</p>`; }
    } catch { chainsHTML = `<p class="empty">Chain data unavailable.</p>`; }
    let fpHTML = "";
    try {
      const [fp, sim] = await Promise.all([
        jget(`/patterns/${id}/fingerprint`),
        jget(`/patterns/${id}/similar?n=5`)]);
      const sims = ((sim || {}).similar || []).map((s) =>
        `<article class="card"><h4>${esc(s.title)}</h4>
         <p><strong>${esc(s.similarity)}% operational signature similarity</strong> (${esc(s.match_class)})</p>
         <ul class="matchlist">${(s.matched || []).map((m) => `<li>✓ ${esc(m)}</li>`).join("")}</ul>
         <button type="button" data-open-pattern="${esc(s.pattern_id)}">View pattern</button></article>`).join("")
        || `<p class="empty">No comparable patterns yet.</p>`;
      fpHTML = `<h4>Operational fingerprint</h4>${fingerprintChips(fp)}
        <h4>Similar operational patterns</h4><div class="cards">${sims}</div>`;
    } catch { fpHTML = `<p class="empty">Fingerprint unavailable.</p>`; }
    const labOpts = members.map((m, n) => {
      const s = Array.isArray(m.delay_series) ? m.delay_series : [];
      return s.length ? `<option value="${esc(m.id)}">Occurrence ${n + 1} — ${esc(fmtT(m.detected_at))} (${s.length} points)</option>` : "";
    }).join("");
    const labHTML = labOpts ? `<h4>Counterfactual lab</h4>
      <p class="fineprint">Explore hypothetical transformations of the observed near-miss. Results are deterministic simulations, not predictions.</p>
      <form class="ivform" data-lab="${esc(id)}">
        <label>Occurrence <select name="near_miss">${labOpts}</select></label>
        <label>Scenario <select name="scenario">
          <option value="REDUCE_PEAK_PERCENT">Reduce peak delay (%)</option>
          <option value="START_RECOVERY_EARLIER">Start recovery earlier (minutes)</option>
          <option value="REDUCE_RECOVERY_DURATION_PERCENT">Reduce recovery duration (%)</option></select></label>
        <label>Parameter <input name="value" inputmode="decimal" required placeholder="e.g. 25"></label>
        <button type="submit">Run simulation</button>
        <span class="formmsg" role="status"></span></form>
      <div data-labresult></div>` : "";
    const invs = (det.investigations || []).map((inv, ii) => {
      const facts = (inv.evidence || []).map(evidenceItem).join("") || `<p class="empty">No evidence recorded for this investigation.</p>`;
      const recs = (inv.recommendations || []).map((r, ri) => {
        const ivs = (r.interventions || []).map((x) => renderIntervention(x, r, id)).join("");
        const form = (r.interventions || []).length ? "" : interventionForm(r, id);
        const copyText = `${r.title}\n${r.description}\nRationale: ${r.rationale || "see evidence"}\nExpected effect: ${r.expected_effect || "—"}\nConfidence: ${r.confidence_score}`;
        return `<h4>RECOMMENDED ACTION: ${esc(r.title)}</h4><p>${esc(r.description)}</p>
          <p><em>Why (agent rationale):</em> ${esc(r.rationale || "Grounded in the evidence above; see investigation record.")}</p>
          <div class="claim INFERENCE"><strong>INFERENCE</strong> — agent assessment confidence ${esc(inv.confidence_score)}: ${esc(inv.investigation_summary || "investigation open")}</div>
          <div class="claim HYPOTHESIS"><strong>HYPOTHESIS (unverified expectation)</strong> — ${esc(r.expected_effect || "effect not yet stated")} · confidence ${esc(r.confidence_score)}</div>
          <p><button type="button" data-copy data-text="${esc(copyText)}">Copy recommendation</button> <span class="copied" role="status"></span></p>
          ${ivs}${form}`;
      }).join("") || `<p class="empty">No recommendation yet — investigation is still open.</p>`;
      return `<h4>AGENT INVESTIGATION — status ${esc(inv.status)} (confidence ${esc(inv.confidence_score)})</h4>
        <p>${esc(inv.investigation_summary || "Evidence gathered; agent reasoning pending.")}</p>
        <p class="fineprint">Claim wording below is summarized from the stored investigation record; every item links to stored evidence.</p>
        <h5>Established facts (stored evidence — select an item to trace its source)</h5>${facts}${recs}`;
    }).join("") || `<p class="empty">No investigation yet for this pattern.</p>`;
    d.innerHTML = `<button type="button" class="back-btn" data-back>← Back to overview</button>
      <h3>${esc(pat.title)}</h3>
      <p>Route ${esc(route)} · ${esc(pat.pattern_type)} · ${esc(pat.recurrence_count)} occurrences · status ${esc(pat.status)}</p>
      <p>${esc(window)} · investigation: ${esc(invStatus)} · mode ${esc(MODE)}</p>
      <p>${esc(pat.description)}</p>
      <h4>Occurrences — this happened repeatedly (${members.length} shown)</h4>${timelineNote}${occs}
      ${fpHTML}
      <div data-chains>${chainsHTML}</div>
      <h4>Early-warning replay <span class="badge replay">HISTORICAL REPLAY</span></h4>
      <p class="fineprint">Historical replay using observed data up to each cutoff. Not a claim of future prediction accuracy.</p>
      <div data-replay><p class="empty">Loading historical replay…</p></div>${labHTML}${invs}`;
    d.querySelector("[data-back]").addEventListener("click", () => {
      $("h-patterns").scrollIntoView();
      $("h-patterns").setAttribute("tabindex", "-1");
      $("h-patterns").focus({ preventScroll: true });
    });
    try {
      const rp = await jget(`/patterns/${id}/early-warning`);
      const rbox = d.querySelector("[data-replay]");
      if (rbox) {
        rbox.innerHTML = renderReplay(rp);
        const sel = rbox.querySelector("[data-rpselect]");
        const rdet = rbox.querySelector("[data-rpdetail]");
        if (sel && rdet) sel.addEventListener("change", () => { rdet.innerHTML = renderReplayPointDetail(rp, Number(sel.value)); });
      }
    } catch { const rbox = d.querySelector("[data-replay]"); if (rbox) rbox.innerHTML = `<p class="empty">Early-warning replay unavailable.</p>`; }
    const evById = {};
    (det.investigations || []).forEach((inv) => (inv.evidence || []).forEach((e) => { evById[e.id] = e; }));
    d.querySelectorAll("details.evdet").forEach((el) => {
      el.addEventListener("toggle", async () => {
        if (!el.open || el.dataset.loaded) return;
        el.dataset.loaded = "1";
        el.querySelector(".evbody").innerHTML = await resolveEvidence(evById[el.dataset.evidence]).catch(() => `<p class="empty">Evidence details unavailable.</p>`);
      });
    });
    d.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", async () => {
      const done = b.parentElement.querySelector(".copied");
      try {
        if (navigator.clipboard) await navigator.clipboard.writeText(b.dataset.text);
        else throw new Error("no clipboard");
        if (done) done.textContent = "Copied";
      } catch { if (done) done.textContent = "Copy unavailable"; }
    }));
    d.querySelectorAll("[data-investigate-chain]").forEach((b) => b.addEventListener("click", async () => {
      const box = d.querySelector(`[data-chainresult="${CSS.escape(b.dataset.investigateChain)}"]`);
      if (!box || b.disabled) return;
      b.disabled = true;
      box.innerHTML = `<p class="empty">Investigating chain…</p>`;
      try {
        const out = await jpost(`/patterns/${id}/chains/investigate`, { chain_key: b.dataset.investigateChain });
        const claims = (out.agent.claims || []).map((cl) => `<div class="claim ${esc(cl.type)}"><strong>${esc(cl.type)}</strong> — ${esc(cl.statement)} <em>(conf ${esc(cl.confidence)})</em></div>`).join("");
        const rec = out.agent.recommendation || {};
        box.innerHTML = `<h5>CHAIN INVESTIGATION (ephemeral — shown, not stored)</h5>
          <p>${esc(out.agent.summary)}</p>${claims}
          <h5>RECOMMENDED ACTION</h5><p><strong>${esc(rec.title)}</strong></p><p>${esc(rec.description)}</p>
          <p><em>Expected effect:</em> ${esc(rec.expected_effect)} · confidence ${esc(rec.confidence)}</p>
          <p class="fineprint">Investigate the upstream relationship; modifying the source is not claimed to fix the target.</p>`;
      } catch (e) {
        box.innerHTML = `<p class="empty">${esc(errMsg(e, "Chain investigation"))}</p>`;
        b.disabled = false;
      }
    }));
    d.querySelectorAll("[data-open-pattern]").forEach((b) => b.addEventListener("click", () => {
      openPattern(b.dataset.openPattern);
      $("h-detail").focus({ preventScroll: true });
      $("h-detail").scrollIntoView();
    }));
    d.querySelectorAll("[data-lab]").forEach((f) => f.addEventListener("submit", async (ev2) => {
      ev2.preventDefault();
      const btn = f.querySelector("button[type=submit]");
      const msg = f.querySelector(".formmsg");
      const box = f.parentElement.querySelector("[data-labresult]");
      if (btn.disabled) return;
      btn.disabled = true;
      msg.textContent = "Simulating…";
      try {
        const fd = new FormData(f);
        const out = await jpost(`/near-misses/${fd.get("near_miss")}/simulate`,
          { scenario: fd.get("scenario"), value: Number(fd.get("value")) });
        if (out.status !== "SIMULATED") {
          box.innerHTML = `<p class="empty">${esc(out.status === "INSUFFICIENT_DATA" ? "Insufficient data for simulation." : "Insufficient simulation resolution for this scenario.")}</p>`;
        } else {
          const o = out.original, s = out.simulated, stamp = String(Date.now());
          box.innerHTML = `<div class="hypo-banner" role="note">HYPOTHETICAL SIMULATION — NOT A PREDICTION</div>
            <h5>Observed</h5>${timelineSVG(o.series, null, `lab-o-${stamp}`)}<p>${esc(occTextSummary(o.series))}</p>
            <h5>Simulated (${esc(out.scenario)} ${esc(out.parameter)})</h5>${timelineSVG(s.series, null, `lab-s-${stamp}`)}<p>${esc(occTextSummary(s.series))}</p>
            <p>Peak ${esc(o.peak)} min → ${esc(s.peak)} min · Recovery ${esc(o.recovery_duration_seconds)}s → ${esc(s.recovery_duration_seconds)}s · Difference ${esc(out.delta.peak_minutes)} min / ${esc(out.delta.recovery_seconds)}s</p>
            <button type="button" data-sandbox="${esc(fd.get("near_miss"))}">Compare all three interventions</button>
            <div data-sandboxresult></div>
            <button type="button" data-labexplain="${esc(fd.get("near_miss"))}">Explain with agent</button>
            <div data-labagent></div>`;
          const eb = box.querySelector("[data-labexplain]");
          eb.addEventListener("click", async () => {
            eb.disabled = true;
            try {
              const ex = await jpost(`/near-misses/${fd.get("near_miss")}/simulate`,
                { scenario: fd.get("scenario"), value: Number(fd.get("value")), explain: true });
              box.querySelector("[data-labagent]").innerHTML = (ex.agent.claims || []).map((cl) =>
                `<div class="claim ${esc(cl.type)}"><strong>${esc(cl.type)}</strong> — ${esc(cl.statement)} <em>(conf ${esc(cl.confidence)})</em></div>`).join("");
            } catch (e) { box.querySelector("[data-labagent]").innerHTML = `<p class="empty">${esc(errMsg(e, "Agent explanation"))}</p>`; eb.disabled = false; }
          });
          const sb = box.querySelector("[data-sandbox]");
          sb.addEventListener("click", async () => {
            if (sb.disabled) return;
            sb.disabled = true;
            const sbox = box.querySelector("[data-sandboxresult]");
            sbox.innerHTML = `<p class="empty">Comparing modeled interventions…</p>`;
            try {
              const cmp = await jpost(`/near-misses/${fd.get("near_miss")}/sandbox`, {});
              const rows = cmp.options.map((o, i) => o.improvement == null
                ? `<tr><td>${esc(o.scenario)} ${esc(o.parameter)}</td><td colspan="3">Not simulable (${esc(o.status)})</td></tr>`
                : `<tr><td>${esc(o.scenario)} ${esc(o.parameter)}${cmp.best && o.scenario === cmp.best.scenario && o.parameter === cmp.best.parameter ? " ★" : ""}</td><td>${esc(o.simulated_peak)} min</td><td>${esc(o.simulated_recovery_seconds)}s</td><td>${esc(o.improvement)}%</td></tr>`).join("");
              sbox.innerHTML = `<h5>INTERVENTION SANDBOX — counterfactual simulation, not a real-world guarantee</h5>
                <table><tr><th scope="col">Scenario</th><th scope="col">Peak</th><th scope="col">Recovery</th><th scope="col">Improvement</th></tr>${rows}</table>
                ${cmp.best ? `<p><strong>BEST MODELED INTERVENTION: ${esc(cmp.best.scenario)} (${esc(cmp.best.parameter)}) — ${esc(cmp.best.improvement)}%</strong></p>
                <p class="fineprint">Under the observed-data simulation, this scenario produces the largest modeled improvement.</p>
                <button type="button" data-sandboxrec="${esc(fd.get("near_miss"))}" data-scenario="${esc(cmp.best.scenario)}" data-value="${esc(cmp.best.parameter)}">Create recommendation from best option</button>
                <span class="formmsg" role="status"></span>` : `<p class="empty">No simulable options.</p>`}`;
              const rb = sbox.querySelector("[data-sandboxrec]");
              if (rb) rb.addEventListener("click", async () => {
                rb.disabled = true;
                const rmsg = sbox.querySelector(".formmsg");
                try {
                  const rec = await jpost(`/near-misses/${fd.get("near_miss")}/sandbox/recommend`,
                    { scenario: rb.dataset.scenario, value: Number(rb.dataset.value) });
                  rmsg.textContent = "Recommendation recorded — reloading investigation…";
                  await openPattern(id);
                } catch (e) { rmsg.textContent = errMsg(e, "Recommendation"); rb.disabled = false; }
              });
            } catch (e) {
              sbox.innerHTML = `<p class="empty">${esc(errMsg(e, "Intervention comparison"))}</p>`;
              sb.disabled = false;
            }
          });
        }
        msg.textContent = "";
      } catch (e) {
        msg.textContent = e.status === 422 ? "Invalid scenario or parameter." : e.status === 404 ? "Near-miss not found." : "Simulation failed.";
      }
      btn.disabled = false;
    }));
    d.querySelectorAll("[data-chaincompare]").forEach((f) => f.addEventListener("submit", async (ev2) => {
      ev2.preventDefault();
      const msg = f.querySelector(".formmsg");
      msg.textContent = "Comparing…";
      try {
        const fd = new FormData(f);
        const q = new URLSearchParams();
        if (fd.get("since")) q.set("since", new Date(fd.get("since")).toISOString());
        if (fd.get("until")) q.set("until", new Date(fd.get("until")).toISOString());
        const ch = await jget(`/patterns/${id}/chains?${q.toString()}`);
        const mine = (ch.chains || []).find((c) => c.key === f.dataset.chaincompare);
        msg.textContent = mine ? `Window occurrences: ${mine.occurrences} (${mine.strength}). No outcome inferred here — verification stays backend-authoritative.` : "No occurrences in that window.";
      } catch (e) { msg.textContent = errMsg(e, "Window comparison"); }
    }));
    d.querySelectorAll("[data-ivform]").forEach((f) => f.addEventListener("submit", async (ev2) => {
      ev2.preventDefault();
      const btn = f.querySelector("button[type=submit]");
      const msg = f.querySelector(".formmsg");
      if (btn.disabled) return;
      btn.disabled = true;
      msg.textContent = "Recording…";
      try {
        const fd = new FormData(f);
        await jpost("/interventions", { recommendation_id: f.dataset.ivform, intervention_type: fd.get("intervention_type"), target: fd.get("target") });
        await openPattern(f.dataset.pattern);
      } catch (e) {
        btn.disabled = false;
        msg.textContent = e.status === 404 ? "Recommendation not found." : e.status === 422 ? "Unsupported intervention type." : "Recording failed.";
      }
    }));
    $("last-update").textContent = "Last update: " + new Date().toLocaleTimeString();
  } catch (e) { d.innerHTML = `<p class="empty">${esc(errMsg(e, "Pattern evidence"))}</p>`; }
}

$("ingest-btn").addEventListener("click", async (ev) => {
  const btn = ev.currentTarget;
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
    await Promise.all([refreshStatus(), refreshOps(), refreshPatterns(), refreshNearMisses(), refreshResilience(), refreshForecast()]);
  } catch {
    $("feed-state").textContent = "Feed: ingestion trigger failed";
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
});

refreshStatus(); refreshOps(); refreshPatterns(); refreshNearMisses(); refreshResilience(); refreshForecast();
setInterval(() => { refreshStatus(); refreshOps(); }, 30000);
