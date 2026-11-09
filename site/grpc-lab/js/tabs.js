// Tab bodies. Each later module registers its renderer here.

const renderers = {};

export function registerTab(name, render) {
  renderers[name] = render;
}

/** Element for one tab of a lesson; ctx = {t, lang, progress, rerender}. */
export function renderTab(name, lesson, ctx) {
  const render = renderers[name];
  if (render) return render(lesson, ctx);
  const p = document.createElement("p");
  p.className = "placeholder-note";
  p.textContent = ctx.t("ui.comingSoon");
  return p;
}
