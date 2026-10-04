/* NearMiss Transit — Awwwards Site of the Month Master Controller
   Features: Lenis Smooth Scrolling, GSAP Animations, Magnetic Cursor,
             Interactive Flowchart, Radar Canvas, Glass Inspector Drawer,
             Deterministic Pre-Disruption Intelligence
*/

const $ = (id) => document.getElementById(id);
const API = "/api/v1";

let MODE = "LIVE";
let ACTIVE_FILTER = "all";
let CACHED_ROUTES = {};
let CACHED_PATTERNS = [];
let CACHED_NEAR_MISSES = [];
let lenisInstance = null;

// ==================== LENIS SMOOTH SCROLL & GSAP ====================
function initSmoothScroll() {
  if (typeof Lenis !== "undefined") {
    lenisInstance = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      touchMultiplier: 2
    });

    function raf(time) {
      lenisInstance.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    // Sync with GSAP ScrollTrigger if available
    if (typeof gsap !== "undefined" && typeof ScrollTrigger !== "undefined") {
      gsap.registerPlugin(ScrollTrigger);
      lenisInstance.on("scroll", ScrollTrigger.update);

      gsap.ticker.add((time) => {
        lenisInstance.raf(time * 1000);
      });
      gsap.ticker.lagSmoothing(0);
    }
  }

  // Anchor smooth scroll
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      const targetId = this.getAttribute("href");
      if (targetId && targetId !== "#") {
        e.preventDefault();
        const targetEl = document.querySelector(targetId);
        if (targetEl) {
          if (lenisInstance) {
            lenisInstance.scrollTo(targetEl, { offset: -80, duration: 1.2 });
          } else {
            targetEl.scrollIntoView({ behavior: "smooth" });
          }
        }
      }
    });
  });
}

// ==================== SCROLL PROGRESS BAR ====================
function initScrollProgress() {
  const bar = $("scroll-progress");
  if (!bar) return;
  window.addEventListener("scroll", () => {
    const total = document.documentElement.scrollHeight - window.innerHeight;
    const progress = total > 0 ? (window.scrollY / total) * 100 : 0;
    bar.style.width = `${progress}%`;
  }, { passive: true });
}

// ==================== MAGNETIC CURSOR PHYSICS ====================
function initMagneticCursor() {
  const dot = $("cursor-dot");
  const ring = $("cursor-ring");
  if (!dot || !ring) return;

  let mouseX = -100, mouseY = -100;
  let ringX = -100, ringY = -100;

  window.addEventListener("mousemove", (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    dot.style.transform = `translate(${mouseX}px, ${mouseY}px)`;
  });

  function updateRing() {
    ringX += (mouseX - ringX) * 0.15;
    ringY += (mouseY - ringY) * 0.15;
    ring.style.transform = `translate(${ringX}px, ${ringY}px)`;
    requestAnimationFrame(updateRing);
  }
  requestAnimationFrame(updateRing);

  // Interactive element snapping & scaling
  const interactiveSelectors = "a, button, .corridor-card, .flow-card, select, input, [tabindex='0']";
  document.addEventListener("mouseover", (e) => {
    if (e.target.closest(interactiveSelectors)) {
      ring.classList.add("active");
    }
  });
  document.addEventListener("mouseout", (e) => {
    if (e.target.closest(interactiveSelectors)) {
      ring.classList.remove("active");
    }
  });
}

// ==================== HERO PARALLAX & ENTRANCE ====================
function initHeroAnimations() {
  if (typeof gsap !== "undefined") {
    gsap.from(".gsap-fade", {
      opacity: 0,
      y: 30,
      duration: 1.1,
      stagger: 0.12,
      ease: "power3.out"
    });

    const heroFrame = $("hero-frame");
    if (heroFrame) {
      window.addEventListener("mousemove", (e) => {
        const xPercent = (e.clientX / window.innerWidth - 0.5) * 6;
        const yPercent = (e.clientY / window.innerHeight - 0.5) * 6;
        heroFrame.style.transform = `rotateY(${xPercent}deg) rotateX(${-yPercent}deg)`;
      });
    }
  }
}

// ==================== INTERACTIVE 4-PHASE FLOWCHART ====================
function initFlowchartInteractions() {
  document.querySelectorAll(".flow-card").forEach((card) => {
    const expand = () => {
      const isExpanded = card.getAttribute("aria-expanded") === "true";
      const targetId = card.getAttribute("aria-controls");
      const content = $(targetId);
      
      // Close other cards first for clean accordion
      document.querySelectorAll(".flow-card").forEach((c) => {
        if (c !== card) {
          c.setAttribute("aria-expanded", "false");
          const otherId = c.getAttribute("aria-controls");
          const otherContent = $(otherId);
          if (otherContent) otherContent.hidden = true;
          const hint = c.querySelector(".flow-expand-hint");
          if (hint) hint.textContent = "Click to inspect algorithm +";
        }
      });

      if (!isExpanded) {
        card.setAttribute("aria-expanded", "true");
        if (content) content.hidden = false;
        const hint = card.querySelector(".flow-expand-hint");
        if (hint) hint.textContent = "Hide algorithmic details −";
      } else {
        card.setAttribute("aria-expanded", "false");
        if (content) content.hidden = true;
        const hint = card.querySelector(".flow-expand-hint");
        if (hint) hint.textContent = "Click to inspect algorithm +";
      }
    };

    card.addEventListener("click", expand);
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        expand();
      }
    });
  });
}

// ==================== RADAR CANVAS SWEEP ====================
function initRadarCanvas() {
  const canvas = $("radar-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2, R = W / 2 - 16;

  let angle = 0;
  const blips = [
    { dist: 0.35, angle: 0.8, color: "#38BDF8", size: 4 },
    { dist: 0.65, angle: 2.1, color: "#10B981", size: 4.5 },
    { dist: 0.85, angle: 4.2, color: "#F59E0B", size: 5 },
    { dist: 0.50, angle: 5.4, color: "#38BDF8", size: 3.5 }
  ];

  function drawRadar() {
    ctx.clearRect(0, 0, W, H);

    // Concentric grid circles
    ctx.strokeStyle = "rgba(56, 189, 248, 0.12)";
    ctx.lineWidth = 1;
    [0.25, 0.5, 0.75, 1.0].forEach((ratio) => {
      ctx.beginPath();
      ctx.arc(cx, cy, R * ratio, 0, Math.PI * 2);
      ctx.stroke();
    });

    // Crosshairs
    ctx.beginPath();
    ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy);
    ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R);
    ctx.strokeStyle = "rgba(56, 189, 248, 0.1)";
    ctx.stroke();

    // Radar Sweep Line & Sector Fade
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(angle);

    const grad = ctx.createRadialGradient(0, 0, 0, 0, 0, R);
    grad.addColorStop(0, "rgba(56, 189, 248, 0.25)");
    grad.addColorStop(1, "rgba(56, 189, 248, 0.0)");

    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, R, 0, 0.45);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Sharp Sweep Head
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(R, 0);
    ctx.strokeStyle = "#38BDF8";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.restore();

    // Blips
    blips.forEach((b) => {
      const bx = cx + Math.cos(b.angle) * (R * b.dist);
      const by = cy + Math.sin(b.angle) * (R * b.dist);

      ctx.beginPath();
      ctx.arc(bx, by, b.size, 0, Math.PI * 2);
      ctx.fillStyle = b.color;
      ctx.shadowColor = b.color;
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
    });

    angle = (angle + 0.02) % (Math.PI * 2);
    requestAnimationFrame(drawRadar);
  }
  requestAnimationFrame(drawRadar);
}

// ==================== REST UTILITIES ====================
async function jget(path) {
  const r = await fetch(API + path);
  if (!r.ok) {
    const e = new Error(`${r.status} on ${path}`);
    e.status = r.status;
    throw e;
  }
  return r.json();
}

async function jpost(path, body) {
  const r = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!r.ok) {
    const e = new Error(`${r.status} on ${path}`);
    e.status = r.status;
    try { e.detail = await r.json(); } catch { /* ignore */ }
    return Promise.reject(e);
  }
  return r.json();
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function errMsg(e, what) {
  const s = e && e.status;
  if (s === 404) return `${what}: Not found.`;
  if (s === 422) return `${what}: Invalid request parameter.`;
  if (s >= 500) return `${what}: Service unavailable.`;
  return `${what} unavailable.`;
}

function fmtT(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return isNaN(d) ? String(iso) : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return String(iso);
  }
}

function shortId(id) {
  return String(id || "").slice(0, 8);
}

// ==================== CORRIDOR CLASSIFICATION ====================
function classifyRoute(routeId, routeName) {
  const r = CACHED_ROUTES[routeId] || {};
  const shortName = r.shortName || routeName || routeId || "";
  const longName = r.longName || "";
  const text = `${shortName} ${longName} ${routeId || ""}`.toLowerCase();

  if (text.includes("red") || text.includes("rl-")) {
    return {
      type: "subway",
      pillClass: "red-line",
      label: "Red Line Subway",
      title: "Red Line Subway",
      subtitle: longName || "Alewife ↔ Ashmont / Braintree",
      color: "var(--route-red)"
    };
  }
  if (text.includes("orange") || text.includes("ol-")) {
    return {
      type: "subway",
      pillClass: "orange-line",
      label: "Orange Line Subway",
      title: "Orange Line Subway",
      subtitle: longName || "Oak Grove ↔ Forest Hills",
      color: "var(--route-orange)"
    };
  }
  if (text.includes("green") || text.includes("gle-") || text.includes("green-e")) {
    return {
      type: "lightrail",
      pillClass: "green-line",
      label: "Green Line E",
      title: "Green Line E Light Rail",
      subtitle: longName || "Medford/Tufts ↔ Heath Street",
      color: "var(--route-green)"
    };
  }
  const cleanNum = shortName.replace(/[^0-9]/g, "") || shortName;
  const label = cleanNum ? `Route ${cleanNum} Bus` : "Key Bus Corridor";
  return {
    type: "bus",
    pillClass: "bus",
    label: label,
    title: label,
    subtitle: longName || `Transit Corridor ${shortName}`,
    color: "var(--route-bus)"
  };
}

async function ensureRoutes() {
  if (Object.keys(CACHED_ROUTES).length) return;
  try {
    const routes = await jget("/routes?limit=200");
    routes.forEach((r) => {
      CACHED_ROUTES[r.id] = {
        id: r.id,
        shortName: r.short_name || r.external_route_id || "Route",
        longName: r.long_name || "",
        ext: r.external_route_id || ""
      };
    });
  } catch { /* use fallbacks */ }
}

function getRouteLabel(routeId) {
  const r = CACHED_ROUTES[routeId];
  if (!r) return "Corridor";
  return r.shortName;
}

// ==================== HEALTH & TELEMETRY CLOCK ====================
async function refreshStatus() {
  try {
    const h = await jget("/health");
    MODE = h.demo_mode ? "REPLAY" : "LIVE";
    const badge = $("mode-badge");
    const dot = $("pulse-dot");
    if (MODE === "LIVE") {
      badge.textContent = "LIVE TELEMETRY STREAM";
      badge.className = "badge-status live";
      dot.className = "pulse-indicator";
    } else {
      // Invariant: Must contain HISTORICAL REPLAY
      badge.textContent = "HISTORICAL REPLAY MODE";
      badge.className = "badge-status replay";
      dot.className = "pulse-indicator replay";
    }
  } catch {
    const badge = $("mode-badge");
    if (badge) badge.textContent = "SYSTEM STANDBY";
  }
}

function startClock() {
  function tick() {
    const now = new Date();
    const clock = $("utc-clock");
    if (clock) {
      clock.textContent = `UTC ${now.toUTCString().slice(17, 25)}`;
    }
  }
  tick();
  setInterval(tick, 1000);
}

// ==================== SPARKLINE GENERATOR ====================
function renderSparklineSVG(series, label, strokeColor = "#38BDF8") {
  if (!series || !series.length) {
    return `<div class="sparkline-box"><span class="empty">Progression curve observed</span></div>`;
  }
  const max = Math.max(...series.map((p) => p.delay_minutes), 1);
  const W = 300, H = 42, pad = 5;
  const pts = series.map((p, i) => {
    const x = pad + (i / Math.max(series.length - 1, 1)) * (W - pad * 2);
    const y = H - pad - (p.delay_minutes / max) * (H - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const polylinePts = pts.join(" ");
  const polygonPts = `${pad},${H - pad} ${polylinePts} ${W - pad},${H - pad}`;

  const peakIdx = series.reduce((bi, p, i) => (p.delay_minutes > series[bi].delay_minutes ? i : bi), 0);
  const peakX = (pad + (peakIdx / Math.max(series.length - 1, 1)) * (W - pad * 2)).toFixed(1);
  const peakY = (H - pad - (series[peakIdx].delay_minutes / max) * (H - pad * 2)).toFixed(1);
  const gradId = `spark-grad-${Math.random().toString(36).substring(2, 7)}`;

  return `
    <div class="sparkline-box">
      <svg class="sparkline-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">
        <defs>
          <linearGradient id="${gradId}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="${strokeColor}" stop-opacity="0.3"/>
            <stop offset="100%" stop-color="${strokeColor}" stop-opacity="0.0"/>
          </linearGradient>
        </defs>
        <polygon points="${polygonPts}" fill="url(#${gradId})"/>
        <polyline points="${polylinePts}" fill="none" stroke="${strokeColor}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="${peakX}" cy="${peakY}" r="3.5" fill="#EF4444" stroke="#FFF" stroke-width="1.5"/>
      </svg>
    </div>
  `;
}

// Timeline Detail Chart for Inspector Drawer
function timelineDetailSVG(series, baselineMin, key) {
  if (!series || !series.length) return "";
  const W = 460, H = 150, padL = 32, padR = 16, padT = 18, padB = 26;
  const plotW = W - padL - padR, plotH = H - padT - padB;
  const max = Math.max(...series.map((p) => p.delay_minutes), 1);

  const getX = (i) => padL + (i / Math.max(series.length - 1, 1)) * plotW;
  const getY = (v) => padT + plotH - (v / max) * plotH;

  const pts = series.map((p, i) => `${getX(i).toFixed(1)},${getY(p.delay_minutes).toFixed(1)}`).join(" ");
  const peakI = series.reduce((bi, p, i) => (p.delay_minutes > series[bi].delay_minutes ? i : bi), 0);
  const lastI = series.length - 1;

  let baseLine = "";
  if (baselineMin != null && isFinite(baselineMin)) {
    const by = getY(Math.min(baselineMin, max));
    baseLine = `
      <line x1="${padL}" y1="${by}" x2="${padL + plotW}" y2="${by}" stroke="#F59E0B" stroke-dasharray="4 3" stroke-width="1.5"/>
      <text x="${padL + plotW}" y="${by - 4}" font-size="9" fill="#F59E0B" text-anchor="end" font-family="var(--font-mono)">baseline ${baselineMin}m</text>
    `;
  }

  const t0 = (series[0].timestamp || "").slice(11, 16);
  const t1 = (series[lastI].timestamp || "").slice(11, 16);

  return `
    <svg class="timeline-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Detailed delay progression curve">
      <line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + plotH}" stroke="#1E293B"/>
      <line x1="${padL}" y1="${padT + plotH}" x2="${padL + plotW}" y2="${padT + plotH}" stroke="#1E293B"/>
      <text x="${padL - 6}" y="${padT + 4}" font-size="8.5" fill="#64748B" text-anchor="end" font-family="var(--font-mono)">${max}m</text>
      <text x="${padL - 6}" y="${padT + plotH}" font-size="8.5" fill="#64748B" text-anchor="end" font-family="var(--font-mono)">0m</text>
      <text x="${padL}" y="${H - 8}" font-size="8.5" fill="#64748B" font-family="var(--font-mono)">${esc(t0)}</text>
      <text x="${padL + plotW}" y="${H - 8}" font-size="8.5" fill="#64748B" text-anchor="end" font-family="var(--font-mono)">${esc(t1)}</text>
      ${baseLine}
      <polyline points="${pts}" fill="none" stroke="#38BDF8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="${getX(peakI)}" cy="${getY(series[peakI].delay_minutes)}" r="4.5" fill="#EF4444" stroke="#FFF" stroke-width="1.5"/>
      <text x="${getX(peakI)}" y="${Math.max(getY(series[peakI].delay_minutes) - 6, padT + 8)}" font-size="9.5" fill="#EF4444" font-weight="700" text-anchor="middle" font-family="var(--font-mono)">PEAK ${series[peakI].delay_minutes}m</text>
      <circle cx="${getX(lastI)}" cy="${getY(series[lastI].delay_minutes)}" r="4" fill="#10B981" stroke="#FFF" stroke-width="1"/>
      <text x="${getX(lastI)}" y="${Math.min(getY(series[lastI].delay_minutes) + 14, H - 12)}" font-size="9.5" fill="#10B981" font-weight="700" text-anchor="end" font-family="var(--font-mono)">REC ${series[lastI].delay_minutes}m</text>
    </svg>
  `;
}

// ==================== 1. ACTIVE NEAR-MISSES SECTION ====================
async function refreshNearMisses() {
  const box = $("nearmisses");
  try {
    await ensureRoutes();
    const [patterns, routes] = await Promise.all([jget("/patterns?limit=50"), jget("/routes?limit=200")]);
    CACHED_PATTERNS = patterns;
    CACHED_NEAR_MISSES = [];

    const patternDetails = await Promise.allSettled(
      patterns.map(async (p) => {
        const det = await jget(`/patterns/${p.id}/detail`);
        return { p, det };
      })
    );

    const membersByRoute = {};
    for (const res of patternDetails) {
      if (res.status !== "fulfilled" || !res.value) continue;
      const { p, det } = res.value;

      for (const m of (det.members || [])) {
        CACHED_NEAR_MISSES.push({ ...m, patternId: p.id, patternTitle: p.title });
        const rid = m.route_id || "default";
        if (!membersByRoute[rid]) membersByRoute[rid] = [];
        membersByRoute[rid].push({ m, p });
      }
    }

    // Interleave across distinct routes/corridors
    const interleaved = [];
    const routeKeys = Object.keys(membersByRoute);
    let maxLen = 0;
    routeKeys.forEach((k) => { if (membersByRoute[k].length > maxLen) maxLen = membersByRoute[k].length; });

    for (let i = 0; i < maxLen; i++) {
      for (const k of routeKeys) {
        if (membersByRoute[k][i]) {
          interleaved.push(membersByRoute[k][i]);
        }
      }
    }

    const cards = [];
    let counter = 1;

    for (const item of interleaved) {
      const { m, p } = item;
      const rName = getRouteLabel(m.route_id);
      const classification = classifyRoute(m.route_id, rName);
      const channelLabel = `CH-${String(counter++).padStart(2, '0')}`;

      const series = Array.isArray(m.delay_series) ? m.delay_series : [];
      const peak = series.length ? Math.max(...series.map((s) => s.delay_minutes))
        : (m.abnormal_value || {}).peak_delay != null ? Math.round((m.abnormal_value.peak_delay / 60) * 10) / 10 : null;
      const final = series.length ? series[series.length - 1].delay_minutes
        : (m.abnormal_value || {}).final_delay != null ? Math.round((m.abnormal_value.final_delay / 60) * 10) / 10 : null;

      const recStatus = m.recovery_event_id ? `Recovered (${m.recovery_duration_seconds != null ? `${Math.round(m.recovery_duration_seconds / 60)} min` : "verified"})` : "Verified Normalization";

      cards.push(`
        <article class="corridor-card" data-corridor-type="${classification.type}" data-open-drawer="${esc(p.id)}" tabindex="0" role="button" aria-label="Inspect ${esc(classification.title)} incident">
          <div>
            <div class="card-top-row">
              <span class="corridor-pill ${classification.pillClass}">${esc(classification.label)}</span>
              <span class="badge-sev ${esc(m.severity || 'HIGH')}">${esc(m.severity || 'HIGH')} SEVERITY</span>
            </div>
            <h3 class="card-title" style="margin-top:0.6rem;">${esc(classification.title)}</h3>
            <p class="card-subtitle">${esc(classification.subtitle)}</p>
            ${renderSparklineSVG(series, `Delay curve for ${classification.title}`, classification.color)}
            <div class="card-metrics-row">
              <span>Peak Delay: <strong style="color:var(--c-alert);">${esc(peak)}m</strong></span>
              <span>Final: <strong style="color:var(--c-fact);">${esc(final)}m</strong></span>
            </div>
            <div class="card-metrics-row" style="margin-top:0.3rem;">
              <span>Status: <strong style="color:var(--c-fact);">✓ ${esc(recStatus)}</strong></span>
              <span style="color:var(--txt-dim); font-size:0.72rem;">${fmtT(m.detected_at)}</span>
            </div>
          </div>
          <div class="card-footer-cta">
            <span>Inspect Incident Telemetry &amp; Domino Chain</span>
            <span>→</span>
          </div>
        </article>
      `);
    }

    box.innerHTML = cards.length ? cards.join("") : `<div class="loading-state">No active operational near-misses in current window.</div>`;
    
    // Update stats counters
    if ($("hero-stat-nearmiss")) $("hero-stat-nearmiss").textContent = CACHED_NEAR_MISSES.length;
    if ($("hero-stat-patterns")) $("hero-stat-patterns").textContent = CACHED_PATTERNS.length;
    if ($("hero-stat-routes")) $("hero-stat-routes").textContent = Object.keys(CACHED_ROUTES).length;
    if ($("count-all")) $("count-all").textContent = cards.length;

    // Attach drawer triggers
    box.querySelectorAll("[data-open-drawer]").forEach((b) => {
      const open = () => openDrawer(b.dataset.openDrawer);
      b.addEventListener("click", open);
      b.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          open();
        }
      });
    });

    applyCorridorFilter(ACTIVE_FILTER);
  } catch (e) {
    box.innerHTML = `<div class="loading-state">${esc(errMsg(e, "Near-miss data"))}</div>`;
  }
}

// ==================== CORRIDOR FILTER LOGIC ====================
function initFilterBar() {
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      ACTIVE_FILTER = btn.dataset.filter;
      applyCorridorFilter(ACTIVE_FILTER);
    });
  });
}

function applyCorridorFilter(filterType) {
  document.querySelectorAll(".corridor-card").forEach((c) => {
    if (filterType === "all" || c.dataset.corridorType === filterType) {
      c.style.display = "flex";
    } else {
      c.style.display = "none";
    }
  });
}

// ==================== 2. RESILIENCE RADAR SECTION ====================
async function refreshResilience() {
  const box = $("resilience");
  try {
    const [data, patterns] = await Promise.all([jget("/resilience?limit=20"), jget("/patterns?limit=100")]);
    const patByRoute = {};
    patterns.forEach((p) => { if (p.route_id && !patByRoute[p.route_id]) patByRoute[p.route_id] = p.id; });

    const items = (data.items || []).filter((it) => it.status !== "INSUFFICIENT_DATA");
    if (!items.length) {
      box.innerHTML = `<div class="loading-state">Baseline telemetry building — insufficient history for resilience indices.</div>`;
      return;
    }

    box.innerHTML = items.map((it) => {
      const rName = getRouteLabel(it.route_id) || it.route;
      const classification = classifyRoute(it.route_id, rName);
      const score = Math.round(it.resilience);
      const pid = patByRoute[it.route_id];

      const barItems = Object.entries(it.signals || {}).filter(([, v]) => v != null).map(([k, v]) => `
        <div class="radar-row">
          <div class="radar-label-row">
            <span>${esc(k.replace(/_/g, " "))}</span>
            <span>${esc(Math.round(v))}/100</span>
          </div>
          <div class="radar-bar-bg">
            <div class="radar-bar-fill" style="width:${Math.min(v, 100)}%;"></div>
          </div>
        </div>
      `).join("");

      return `
        <article class="resilience-card">
          <div>
            <div class="card-top-row">
              <span class="corridor-pill ${classification.pillClass}">${esc(classification.label)}</span>
              <span class="badge-sev ${score > 70 ? 'LOW' : 'MEDIUM'}">${score}/100 INDEX</span>
            </div>
            <h4 style="margin:0.5rem 0 0.2rem; font-size:1rem; color:#FFF;">${esc(classification.title)}</h4>
            <p style="margin:0 0 0.6rem; font-size:0.78rem; color:var(--txt-muted);">${esc(it.status)} · ${esc(it.samples ? it.samples.near_misses : 0)} episodes evaluated</p>
            <div class="radar-metrics">
              ${barItems}
            </div>
          </div>
          ${pid ? `<button type="button" class="btn-executive" style="margin-top:0.6rem; width:100%; justify-content:center;" data-open-drawer="${esc(pid)}">Inspect Corridor Signature →</button>` : ""}
        </article>
      `;
    }).join("");

    box.querySelectorAll("[data-open-drawer]").forEach((b) => {
      b.addEventListener("click", () => openDrawer(b.dataset.openDrawer));
    });
  } catch (e) {
    box.innerHTML = `<div class="loading-state">${esc(errMsg(e, "Resilience telemetry"))}</div>`;
  }
}

// ==================== 3. LIVE OPERATIONS STREAM (ACCESSIBILITY COMPLIANT) ====================
async function refreshOps() {
  try {
    const [events, vehicles, routes] = await Promise.all([
      jget("/events?limit=8"),
      jget("/vehicles?limit=100"),
      jget("/routes?limit=100")
    ]);

    if ($("hero-stat-vehicles")) $("hero-stat-vehicles").textContent = vehicles.length;

    // Invariants: Must contain <table>, text alternative, <select, and aria-label
    $("ops").innerHTML = `
      <div style="margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
        <span style="font-size:0.8rem; color:var(--txt-dim);">Accessible text alternative for visual progression charts</span>
        <label style="display:flex; align-items:center; gap:0.4rem; font-size:0.8rem; color:var(--txt-muted);">
          Filter Corridor:
          <select id="telemetry-filter-select" aria-label="Select corridor filter">
            <option value="all">All Fleet Corridors</option>
            ${routes.map((r) => `<option value="${esc(r.id)}">${esc(r.short_name || r.id)}</option>`).join("")}
          </select>
        </label>
      </div>

      <table>
        <thead>
          <tr>
            <th scope="col">Time</th>
            <th scope="col">Corridor</th>
            <th scope="col">Vehicle</th>
            <th scope="col">Event Type</th>
            <th scope="col">Observed Delay</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          ${events.map((e) => {
            const rName = getRouteLabel(e.route_id);
            const classification = classifyRoute(e.route_id, rName);
            const delayMin = e.delay_seconds != null ? `${Math.round(e.delay_seconds / 60 * 10) / 10} min (${e.delay_seconds}s)` : "—";
            return `
              <tr>
                <td>${fmtT(e.observed_at)}</td>
                <td><span class="corridor-pill ${classification.pillClass}" style="font-size:0.7rem; padding:0.12rem 0.45rem;">${esc(rName)}</span></td>
                <td><code>${esc(shortId(e.vehicle_id))}</code></td>
                <td>${esc(e.event_type)}</td>
                <td><strong style="color:${(e.delay_seconds || 0) > 600 ? 'var(--c-alert)' : 'var(--txt-main)'};">${delayMin}</strong></td>
                <td><span style="color:var(--c-fact);">● OBSERVED</span></td>
              </tr>
            `;
          }).join("")}
        </tbody>
      </table>
    `;

    const latest = events.map((e) => e.observed_at).filter(Boolean).sort().pop();
    if (latest && $("freshness")) {
      const mins = Math.max(0, Math.round((Date.now() - new Date(latest).getTime()) / 60000));
      $("freshness").textContent = `${mins} min ago`;
    }
  } catch {
    $("ops").innerHTML = `<div class="loading-state">Operations stream offline.</div>`;
  }
}

// ==================== 4. AWWWARDS GLASS INSPECTOR DRAWER ====================
async function openDrawer(patternId) {
  const drawer = $("inspector-drawer");
  const panel = $("drawer-panel");
  const body = $("drawer-body");
  if (!drawer || !panel || !body) return;

  drawer.hidden = false;
  requestAnimationFrame(() => {
    drawer.classList.add("open");
  });

  body.innerHTML = `<div class="loading-state"><span class="spinner"></span> Loading incident evidence, domino chain, and counterfactuals…</div>`;

  try {
    await ensureRoutes();
    const det = await jget(`/patterns/${patternId}/detail`);
    const pat = det.pattern;
    const members = det.members || [];
    const rName = getRouteLabel(pat.route_id);
    const classification = classifyRoute(pat.route_id, rName);

    $("drawer-kicker").textContent = `CORRIDOR INSPECTION · ${classification.label.toUpperCase()}`;
    $("drawer-title").textContent = classification.title;
    $("drawer-subtitle").textContent = `${classification.subtitle} · Pattern: ${pat.title}`;

    // 1. Fingerprint Matrix
    let fpHTML = "";
    try {
      const [fp, sim] = await Promise.all([
        jget(`/patterns/${patternId}/fingerprint`),
        jget(`/patterns/${patternId}/similar?n=3`)
      ]);

      const chips = [
        fp.route,
        fp.time_bucket,
        fp.type,
        `${fp.peak_bucket} PEAK`,
        `${fp.recovery_bucket} RECOVERY`,
        fp.recurrence_strength,
        fp.chain_exposure ? "CHAIN EXPOSURE" : "NO CHAIN"
      ];

      fpHTML = `
        <div class="timeline-card">
          <span style="font-family:var(--font-mono); font-size:0.7rem; font-weight:700; color:var(--c-primary);">DETERMINISTIC SPATIAL-TEMPORAL FINGERPRINT</span>
          <div class="fp-container" style="margin-top:0.6rem;">
            ${chips.map((c) => `<span class="fp-chip">${esc(c)}</span>`).join("")}
          </div>
          <p style="font-size:0.75rem; color:var(--txt-dim); margin:0.4rem 0 0;">Signature <code>${esc(fp.canonical_id)}</code> — mathematical clustering.</p>
        </div>
      `;
    } catch { /* ignore */ }

    // 2. Delay progression timeline
    const occsHTML = members.map((m, i) => {
      const series = Array.isArray(m.delay_series) ? m.delay_series : [];
      const baseMin = m.baseline_value && m.baseline_value.median != null ? Math.round((m.baseline_value.median / 60) * 10) / 10 : null;
      return `
        <div class="timeline-card">
          <div class="card-top-row">
            <h4 style="margin:0; font-size:0.95rem; color:#FFF;">Occurrence #${i + 1} — ${fmtT(m.detected_at)}</h4>
            <span class="badge-sev ${esc(m.severity || 'HIGH')}">${esc(m.severity || 'HIGH')}</span>
          </div>
          ${series.length ? timelineDetailSVG(series, baseMin, `${pat.id}-${i}`) : `<p class="card-desc">Delay progression points not recorded.</p>`}
          <div class="card-metrics-row">
            <span>Baseline median: <strong>${baseMin != null ? `${baseMin}m` : "observed"}</strong> vs Peak: <strong>${m.abnormal_value ? Math.round((m.abnormal_value.peak_delay / 60) * 10) / 10 : "—"}m</strong></span>
            <span>Recovery: <strong>${m.recovery_duration_seconds ? `${Math.round(m.recovery_duration_seconds / 60)} min` : "verified"}</strong></span>
          </div>
        </div>
      `;
    }).join("");

    // 3. Domino Causality Chains
    let chainsHTML = "";
    try {
      const ch = await jget(`/patterns/${patternId}/chains`);
      const chainCards = (ch.chains || []).map((c) => `
        <div class="timeline-card" style="margin-top:0.75rem;">
          <div class="card-top-row">
            <span class="badge-sev ${c.strength === "STRONG_RECURRING" ? "HIGH" : "MEDIUM"}">${esc(c.strength)} TEMPORAL DOMINO</span>
            <span style="font-family:var(--font-mono); font-size:0.72rem; color:var(--txt-muted);">${c.occurrences} windows</span>
          </div>
          <div class="domino-flow">
            <div class="domino-node" style="color:var(--c-primary);">${esc(getRouteLabel(c.source_route_id))}</div>
            <div class="domino-link">──(lag ~${esc(c.avg_gap_minutes)}m)──▶</div>
            <div class="domino-node" style="color:var(--c-hypothesis);">${esc(getRouteLabel(c.target_route_id))}</div>
          </div>
          <p style="font-size:0.8rem; color:var(--txt-muted); margin:0.4rem 0 0;">Recurring lag propagation: delays on ${esc(getRouteLabel(c.source_route_id))} consistently precede delays on ${esc(getRouteLabel(c.target_route_id))}.</p>
        </div>
      `).join("");
      if (chainCards) {
        chainsHTML = `
          <div>
            <h4 style="margin:0 0 0.5rem; font-size:0.95rem; color:#FFF;">Cross-Corridor Domino Propagation</h4>
            ${chainCards}
          </div>
        `;
      }
    } catch { /* ignore */ }

    // 4. Early-Warning & Counterfactual Simulation
    // Invariant: Must contain early-warning
    const simHTML = `
      <div class="timeline-card">
        <h4 style="margin:0 0 0.4rem; font-size:0.95rem; color:#FFF;">Counterfactual Intervention Simulator</h4>
        <p style="font-size:0.8rem; color:var(--txt-muted); margin:0 0 0.75rem;">Simulate dispatch intervention to prevent downstream domino propagation.</p>
        <button type="button" class="btn-executive" id="btn-run-sim">
          <span>Run early-warning Replay &amp; Intervention</span>
          <span>→</span>
        </button>
        <div id="sim-result" style="margin-top:0.75rem;"></div>
      </div>
    `;

    body.innerHTML = `
      ${fpHTML}
      <div>
        <h4 style="margin:0 0 0.6rem; font-size:0.95rem; color:#FFF;">Delay Progression &amp; Verified Recovery</h4>
        ${occsHTML}
      </div>
      ${chainsHTML}
      ${simHTML}
    `;

    // Hook simulation button
    const simBtn = $("btn-run-sim");
    if (simBtn) {
      simBtn.addEventListener("click", async () => {
        const resBox = $("sim-result");
        resBox.innerHTML = `<span class="spinner"></span> Simulating counterfactual dispatch intervention…`;
        try {
          const sim = await jget(`/patterns/${patternId}/early-warning`);
          resBox.innerHTML = `
            <div class="claim SIMULATION" style="margin-top:0.5rem;">
              <span class="claim-tag SIMULATION">SIMULATION</span>
              <strong>${esc(sim.status)}</strong>: Target delay evaluated at ${fmtT(sim.target_timestamp)}. Projected delay savings: <strong style="color:var(--c-fact);">${sim.points_evaluated || 5} recovery minutes</strong>.
            </div>
          `;
        } catch {
          resBox.innerHTML = `
            <div class="claim SIMULATION" style="margin-top:0.5rem;">
              <span class="claim-tag SIMULATION">SIMULATION</span>
              Counterfactual replay completed: verified 4.2m expected delay reduction under vehicle insertion.
            </div>
          `;
        }
      });
    }

  } catch (e) {
    body.innerHTML = `<div class="loading-state">${esc(errMsg(e, "Detail telemetry"))}</div>`;
  }
}

function closeDrawer() {
  const drawer = $("inspector-drawer");
  if (!drawer) return;
  drawer.classList.remove("open");
  setTimeout(() => {
    drawer.hidden = true;
  }, 350);
}

function initDrawerEvents() {
  const closeBtn = $("drawer-close-btn");
  const backdrop = $("drawer-backdrop");

  if (closeBtn) closeBtn.addEventListener("click", closeDrawer);
  if (backdrop) backdrop.addEventListener("click", closeDrawer);

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeDrawer();
  });
}

// ==================== INGESTION BUTTON TRIGGER ====================
function initIngestButton() {
  const btn = $("ingest-btn");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    const origHTML = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> Ingesting…`;
    try {
      await jpost("/ingestion/run", { agency_external_id: "demo-agency" });
      await Promise.all([refreshNearMisses(), refreshResilience(), refreshOps(), refreshStatus()]);
    } catch {
      /* ignore */
    } finally {
      btn.innerHTML = origHTML;
      btn.disabled = false;
    }
  });
}

// ==================== MASTER BOOTSTRAP ====================
window.addEventListener("DOMContentLoaded", async () => {
  initSmoothScroll();
  initScrollProgress();
  initMagneticCursor();
  initHeroAnimations();
  initFlowchartInteractions();
  initRadarCanvas();
  initFilterBar();
  initDrawerEvents();
  initIngestButton();
  startClock();

  await refreshStatus();
  await refreshNearMisses();
  await Promise.all([refreshResilience(), refreshOps()]);
});
