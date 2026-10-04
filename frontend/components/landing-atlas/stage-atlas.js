/* Landing stage atlas component: interactive deviation-escalation-recovery tabs and animated disclosure panels */

function initStageAtlas() {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const stages = [
    [
      "01 / Deviation",
      "Something shifts.",
      "Service moves away from its expected rhythm. A small deviation becomes the first piece of evidence, not an alarm on its own.",
    ],
    [
      "02 / Escalation",
      "The pressure builds.",
      "The deviation intensifies within the observation window. Its shape and timing help distinguish an operational near-miss from routine variation.",
    ],
    [
      "03 / Recovery",
      "Service finds its rhythm.",
      "The service recovers, but the evidence remains. This complete sequence can be compared with past events to reveal what keeps recurring.",
    ],
  ];
  const tabs = [...document.querySelectorAll(".stage-tab")];
  let detailAnimation;

  function selectStage(index) {
    const atlas = document.querySelector(".atlas");
    if (!atlas) return;
    atlas.dataset.stage = index;
    tabs.forEach((tab, i) => {
      tab.setAttribute("aria-selected", String(index === i));
      tab.tabIndex = index === i ? 0 : -1;
    });
    const panel = document.querySelector("#stage-panel");
    if (!panel) return;
    panel.setAttribute("aria-labelledby", `stage-${index}`);
    ["stage-kicker", "stage-title", "stage-copy"].forEach((id, i) => {
      const el = document.getElementById(id);
      if (el) el.textContent = stages[index][i];
    });
    detailAnimation?.cancel();
    if (!reduced.matches) {
      detailAnimation = panel.animate(
        [
          { opacity: 0.2, transform: "translateY(8px)" },
          { opacity: 1, transform: "translateY(0)" },
        ],
        { duration: 420, easing: "cubic-bezier(.22,1,.36,1)" }
      );
    }
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => selectStage(i));
    tab.addEventListener("keydown", (e) => {
      let next;
      if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
      if (e.key === "ArrowLeft") next = (i + tabs.length - 1) % tabs.length;
      if (e.key === "Home") next = 0;
      if (e.key === "End") next = tabs.length - 1;
      if (next !== undefined) {
        e.preventDefault();
        selectStage(next);
        tabs[next].focus();
      }
    });
  });

  const animations = new WeakMap();
  document.querySelectorAll(".disclosure button").forEach((button) => {
    button.addEventListener("click", () => {
      const panel = document.getElementById(button.getAttribute("aria-controls"));
      if (!panel) return;
      const open = button.getAttribute("aria-expanded") !== "true";
      button.setAttribute("aria-expanded", String(open));
      animations.get(panel)?.cancel();
      panel.hidden = false;
      panel.inert = !open;
      if (reduced.matches) {
        panel.hidden = !open;
        return;
      }
      const animation = panel.animate(
        open
          ? [
              { opacity: 0, transform: "translateY(-8px)" },
              { opacity: 1, transform: "translateY(0)" },
            ]
          : [
              { opacity: 1, transform: "translateY(0)" },
              { opacity: 0, transform: "translateY(-8px)" },
            ],
        { duration: 250, easing: "ease-out" }
      );
      animations.set(panel, animation);
      animation.onfinish = () => {
        if (button.getAttribute("aria-expanded") === "false") panel.hidden = true;
        window.nearmissScroll?.resize();
      };
    });
  });

  // Preserve existing bookmarks after moving the dashboard to its own workspace.
  if (/^#(overview|nearmisses|patterns|investigation|operations)$/.test(location.hash)) {
    location.replace("/workspace" + location.hash);
  }
}
