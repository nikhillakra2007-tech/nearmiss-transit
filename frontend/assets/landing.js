(() => {
  'use strict';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let lenis;
  const setupScroll = () => {
    lenis?.destroy();
    lenis = !reduced.matches && window.Lenis ? new Lenis({ autoRaf: true, lerp: .09, smoothWheel: true, anchors: { offset: -30 } }) : null;
    window.nearmissScroll = lenis;
  };
  setupScroll();
  reduced.addEventListener('change', setupScroll);
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.nav-links');
  function closeMenu() { menu.setAttribute('aria-expanded', 'false'); nav.classList.remove('open'); }
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('open', open);
  });
  nav.addEventListener('click', e => { if (e.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav.classList.contains('open')) { closeMenu(); menu.focus(); } });
  document.addEventListener('click', e => { if (!e.target.closest('.site-nav')) closeMenu(); });

  // Reveal again on reverse scroll. Essential content stays readable without JavaScript.
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => entry.target.classList.toggle('in-view', entry.isIntersecting));
  }, { threshold: .08 });
  document.querySelectorAll('[data-reveal]').forEach(el => observer.observe(el));
  document.body.classList.add('motion-ready');

  const scene = document.querySelector('.network-scene');
  const map = document.querySelector('.network-map');
  const card = document.querySelector('.signal-card');
  let frame = 0;
  function paintDepth() {
    frame = 0;
    if (reduced.matches) { map.style.transform = ''; card.style.transform = ''; return; }
    const box = scene.getBoundingClientRect();
    if (box.bottom < 0 || box.top > innerHeight) return;
    const progress = Math.max(0, Math.min(1, scrollY / 650));
    map.style.transform = `translate3d(0, ${progress * 14}px, 0)`;
    card.style.transform = `translate3d(0, ${progress * -16}px, 0)`;
  }
  function schedulePaint() { if (!frame) frame = requestAnimationFrame(paintDepth); }
  window.addEventListener('scroll', schedulePaint, { passive: true });
  reduced.addEventListener('change', schedulePaint);
  const stages = [
    ['01 / Deviation', 'Something shifts.', 'Service moves away from its expected rhythm. A small deviation becomes the first piece of evidence, not an alarm on its own.'],
    ['02 / Escalation', 'The pressure builds.', 'The deviation intensifies within the observation window. Its shape and timing help distinguish an operational near-miss from routine variation.'],
    ['03 / Recovery', 'Service finds its rhythm.', 'The service recovers, but the evidence remains. This complete sequence can be compared with past events to reveal what keeps recurring.']
  ];
  const tabs = [...document.querySelectorAll('.stage-tab')];
  let detailAnimation;
  function selectStage(index) {
    document.querySelector('.atlas').dataset.stage = index;
    tabs.forEach((tab, i) => { tab.setAttribute('aria-selected', String(index === i)); tab.tabIndex = index === i ? 0 : -1; });
    const panel = document.querySelector('#stage-panel');
    panel.setAttribute('aria-labelledby', `stage-${index}`);
    ['stage-kicker', 'stage-title', 'stage-copy'].forEach((id, i) => { document.getElementById(id).textContent = stages[index][i]; });
    detailAnimation?.cancel();
    if (!reduced.matches) detailAnimation = panel.animate([{ opacity: .2, transform: 'translateY(8px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 420, easing: 'cubic-bezier(.22,1,.36,1)' });
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => selectStage(i));
    tab.addEventListener('keydown', e => {
      let next;
      if (e.key === 'ArrowRight') next = (i + 1) % tabs.length;
      if (e.key === 'ArrowLeft') next = (i + tabs.length - 1) % tabs.length;
      if (e.key === 'Home') next = 0;
      if (e.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { e.preventDefault(); selectStage(next); tabs[next].focus(); }
    });
  });
  const animations = new WeakMap();
  document.querySelectorAll('.disclosure button').forEach(button => {
    button.addEventListener('click', () => {
      const panel = document.getElementById(button.getAttribute('aria-controls'));
      const open = button.getAttribute('aria-expanded') !== 'true';
      button.setAttribute('aria-expanded', String(open));
      animations.get(panel)?.cancel();
      panel.hidden = false;
      panel.inert = !open;
      if (reduced.matches) { panel.hidden = !open; return; }
      const animation = panel.animate(open ? [{ opacity: 0, transform: 'translateY(-8px)' }, { opacity: 1, transform: 'translateY(0)' }] : [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(-8px)' }], { duration: 250, easing: 'ease-out' });
      animations.set(panel, animation);
      animation.onfinish = () => { if (button.getAttribute('aria-expanded') === 'false') panel.hidden = true; lenis?.resize(); };
    });
  });
  // Preserve existing bookmarks after moving the dashboard to its own workspace.
  if (/^#(overview|nearmisses|patterns|investigation|operations)$/.test(location.hash)) location.replace('/workspace' + location.hash);
})();
