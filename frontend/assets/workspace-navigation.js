(() => {
  const names = ['nearmisses', 'resilience', 'overview', 'patterns', 'investigation', 'operations'];
  const sections = [...document.querySelectorAll('main > section')];
  const links = [...document.querySelectorAll('.pagenav a')];
  document.querySelector('.pagenav').setAttribute('role', 'tablist');
  function select(name, focus = false) {
    const index = Math.max(0, names.indexOf(name));
    sections.forEach((section, i) => { section.hidden = i !== index; section.classList.toggle('active', i === index); });
    links.forEach((link, i) => { link.setAttribute('aria-selected', String(i === index)); link.tabIndex = i === index ? 0 : -1; });
    history.replaceState(null, '', '#' + names[index]);
    if (focus) sections[index].querySelector('h2').focus({preventScroll:true});
  }
  sections.forEach((section, i) => {
    section.id = 'view-' + names[i]; section.setAttribute('role', 'tabpanel'); section.setAttribute('aria-labelledby', 'workspace-tab-' + names[i]);
    section.querySelector('h2').tabIndex = -1;
    links[i].id = 'workspace-tab-' + names[i]; links[i].href = '#' + names[i]; links[i].classList.add('section-tab'); links[i].dataset.view = names[i]; links[i].setAttribute('role','tab'); links[i].setAttribute('aria-controls', section.id);
    links[i].addEventListener('click', e => { e.preventDefault(); select(names[i]); });
    links[i].addEventListener('keydown', e => { let next; if(e.key==='ArrowRight')next=(i+1)%names.length; if(e.key==='ArrowLeft')next=(i+names.length-1)%names.length; if(e.key==='Home')next=0; if(e.key==='End')next=names.length-1; if(next!==undefined){e.preventDefault();select(names[next]);links[next].focus();} });
  });
  const original = window.openPattern;
  if (original) window.openPattern = async (...args) => { select('investigation', true); return original(...args); };
  window.addEventListener('hashchange', () => select(location.hash.slice(1)));
  select(location.hash.slice(1) || 'nearmisses');
})();
