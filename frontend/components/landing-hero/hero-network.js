/* Landing Hero Network component: parallax depth layers, responsive mobile menu, and smooth scrolling */

function initLandingHero() {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  let lenis;
  const setupScroll = () => {
    lenis?.destroy();
    lenis =
      !reduced.matches && window.Lenis
        ? new Lenis({
            autoRaf: true,
            lerp: 0.09,
            smoothWheel: true,
            anchors: { offset: -30 },
          })
        : null;
    window.nearmissScroll = lenis;
  };
  setupScroll();
  reduced.addEventListener("change", setupScroll);

  const menu = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav-links");
  function closeMenu() {
    if (!menu || !nav) return;
    menu.setAttribute("aria-expanded", "false");
    nav.classList.remove("open");
  }

  if (menu && nav) {
    menu.addEventListener("click", () => {
      const open = menu.getAttribute("aria-expanded") !== "true";
      menu.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("open", open);
    });
    nav.addEventListener("click", (e) => {
      if (e.target.closest("a")) closeMenu();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && nav.classList.contains("open")) {
        closeMenu();
        menu.focus();
      }
    });
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".site-nav")) closeMenu();
    });
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) =>
        entry.target.classList.toggle("in-view", entry.isIntersecting)
      );
    },
    { threshold: 0.08 }
  );
  document.querySelectorAll("[data-reveal]").forEach((el) => observer.observe(el));
  document.body.classList.add("motion-ready");

  const scene = document.querySelector(".network-scene");
  const map = document.querySelector(".network-map");
  const card = document.querySelector(".signal-card");
  let frame = 0;
  function paintDepth() {
    frame = 0;
    if (reduced.matches || !scene || !map || !card) {
      if (map) map.style.transform = "";
      if (card) card.style.transform = "";
      return;
    }
    const box = scene.getBoundingClientRect();
    if (box.bottom < 0 || box.top > innerHeight) return;
    const progress = Math.max(0, Math.min(1, scrollY / 650));
    map.style.transform = `translate3d(0, ${progress * 14}px, 0)`;
    card.style.transform = `translate3d(0, ${progress * -16}px, 0)`;
  }
  function schedulePaint() {
    if (!frame) frame = requestAnimationFrame(paintDepth);
  }
  window.addEventListener("scroll", schedulePaint, { passive: true });
  reduced.addEventListener("change", schedulePaint);
}
