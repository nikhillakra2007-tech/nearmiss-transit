/* Workspace navigation component: section highlight, skip links, and smooth target focus */

function initWorkspaceNav() {
  const navLinks = document.querySelectorAll(".pagenav a");
  const sections = document.querySelectorAll("main section");

  if (!sections.length || !navLinks.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.querySelector("h2")?.id;
          if (id) {
            navLinks.forEach((link) => {
              link.classList.toggle(
                "active",
                link.getAttribute("href") === `#${id}`
              );
            });
          }
        }
      });
    },
    { threshold: 0.2 }
  );

  sections.forEach((s) => observer.observe(s));
}
