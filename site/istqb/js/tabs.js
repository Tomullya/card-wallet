// Renderers for section tabs and for whole pages (home, chapter, glossary, exam).
// Each later module registers itself here.

const tabs = {};
const pages = {};

export function registerTab(name, render) {
  tabs[name] = render;
}

export function registerPage(name, render) {
  pages[name] = render;
}

function placeholder(ctx) {
  const p = document.createElement("p");
  p.className = "placeholder-note";
  p.textContent = ctx.t("ui.comingSoon");
  return p;
}

/** Element for one tab of a section; ctx = {t, lang, progress, syllabus, section, ...}. */
export function renderTab(name, ctx) {
  return tabs[name] && ctx.section ? tabs[name](ctx) : placeholder(ctx);
}

export function renderPage(name, ctx) {
  return pages[name] ? pages[name](ctx) : placeholder(ctx);
}
