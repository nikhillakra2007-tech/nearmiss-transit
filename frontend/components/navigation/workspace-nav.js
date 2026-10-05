/* Workspace navigation component: section switching, isolated section views, and tab controls */

const SECTION_ALIASES = {
  nearmisses: "nearmisses",
  "h-nearmisses": "nearmisses",
  "active-nearmisses": "nearmisses",

  delays: "delays",
  ops: "delays",
  "h-ops": "delays",
  operations: "delays",
  "time-delays": "delays",
  timedelay: "delays",
  "dime-delay": "delays",

  patterns: "patterns",
  "h-patterns": "patterns",
  recurring: "patterns",

  detail: "detail",
  "h-detail": "detail",
  investigation: "detail",

  forecast: "forecast",
  "h-forecast": "forecast",
  emerging: "forecast",
  overview: "forecast",

  resilience: "resilience",
  "h-resilience": "resilience",
};

function switchSection(targetKey, updateHistory = true) {
  if (!targetKey) targetKey = "nearmisses";
  const rawKey = String(targetKey).replace(/^#/, "").toLowerCase();
  const canonical = SECTION_ALIASES[rawKey] || "nearmisses";

  // Enforce document-level attribute for zero-flash CSS isolation
  try {
    document.documentElement.setAttribute("data-active-section", canonical);
  } catch (_) {}

  const allSections = document.querySelectorAll("main > section");
  const navLinks = document.querySelectorAll(".pagenav a");

  let activeSectionFound = false;

  allSections.forEach((sec) => {
    const secKey = (sec.dataset.section || sec.id.replace("section-", "")).toLowerCase();
    const isTarget = secKey === canonical || sec.id === `section-${canonical}` || sec.id === canonical;

    if (isTarget) {
      sec.removeAttribute("hidden");
      sec.classList.add("active");
      sec.style.display = "block";
      activeSectionFound = true;
      const heading = sec.querySelector("h2");
      if (heading) {
        heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
      }
    } else {
      sec.setAttribute("hidden", "");
      sec.classList.remove("active");
      sec.style.display = "none";
    }
  });

  navLinks.forEach((link) => {
    const href = (link.getAttribute("href") || "").replace(/^#/, "").toLowerCase();
    const linkTarget = SECTION_ALIASES[href] || href;
    const isSelected = linkTarget === canonical || link.id === `tab-${canonical}`;

    link.setAttribute("aria-selected", isSelected ? "true" : "false");
    link.classList.toggle("active", isSelected);
    link.tabIndex = isSelected ? 0 : -1;
  });

  window.scrollTo({ top: 0, behavior: "instant" });

  if (updateHistory && history.replaceState) {
    history.replaceState(null, "", `#${canonical}`);
  }

  return activeSectionFound;
}

// Expose globally for cross-component tab switching
window.switchSection = switchSection;

function initWorkspaceNav() {
  const navLinks = document.querySelectorAll(".pagenav a");
  if (!navLinks.length) return;

  navLinks.forEach((link, idx) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const href = link.getAttribute("href") || "";
      const target = href.replace(/^#/, "");
      switchSection(target, true);
    });

    link.addEventListener("keydown", (e) => {
      let nextIdx;
      if (e.key === "ArrowRight") nextIdx = (idx + 1) % navLinks.length;
      if (e.key === "ArrowLeft") nextIdx = (idx + navLinks.length - 1) % navLinks.length;
      if (e.key === "Home") nextIdx = 0;
      if (e.key === "End") nextIdx = navLinks.length - 1;
      if (nextIdx !== undefined) {
        e.preventDefault();
        navLinks[nextIdx].click();
        navLinks[nextIdx].focus();
      }
    });
  });

  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.slice(1);
    if (hash) {
      switchSection(hash, false);
    }
  });

  // Handle initial page load: if hash provided, open that section; otherwise default to nearmisses
  const initialHash = window.location.hash.slice(1);
  switchSection(initialHash || "nearmisses", false);
}
