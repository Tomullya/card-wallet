// Shell: lesson menu, tabs, routing (#/<lesson>/<tab>), language and theme switches.

import { applyStatic, lang, loadI18n, setLang, t } from "./i18n.js";
import * as progress from "./progress.js";
import { renderTab } from "./tabs.js";

export const TABS = ["comic", "theory", "diagram", "sandbox", "quiz", "practice"];
let lessons = [];

const $ = (id) => document.getElementById(id);

function route() {
  const [, lesson, tab] = location.hash.match(/^#\/(\d\d)\/(\w+)$/) ?? [];
  const known = lessons.some((l) => l.id === lesson) && TABS.includes(tab);
  return known ? { lesson, tab } : { lesson: "00", tab: "comic" };
}

function go(lesson, tab) {
  const target = `#/${lesson}/${tab}`;
  if (location.hash === target) render();
  else location.hash = target;
}

function renderMenu(current) {
  const done = progress.get().lessons;
  $("lesson-list").replaceChildren(
    ...lessons.map((l) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#/${l.id}/comic`;
      a.dataset.testid = `lesson-${l.id}`;
      a.className = "lessons__link";
      if (l.id === current) a.setAttribute("aria-current", "page");
      const num = document.createElement("span");
      num.className = "lessons__num";
      num.textContent = l.id;
      const name = document.createElement("span");
      name.className = "lessons__name";
      name.textContent = t(`lesson.${l.id}.title`);
      a.append(num, name);
      if (done[l.id]?.done) {
        const mark = document.createElement("span");
        mark.className = "lessons__done";
        mark.dataset.testid = `done-${l.id}`;
        mark.setAttribute("aria-label", t("ui.done"));
        mark.textContent = "✓";
        a.append(mark);
      }
      li.append(a);
      return li;
    }),
  );
  const count = Object.values(done).filter((x) => x.done).length;
  $("progress-note").textContent = t("ui.progress", { n: count, total: lessons.length });
}

function renderTabs(lesson, current) {
  $("tab-list").replaceChildren(
    ...TABS.map((name) => {
      const b = document.createElement("button");
      b.type = "button";
      b.role = "tab";
      b.id = `tab-${name}`;
      b.dataset.testid = `tab-${name}`;
      b.setAttribute("aria-selected", String(name === current));
      b.setAttribute("aria-controls", "panel");
      b.tabIndex = name === current ? 0 : -1;
      b.textContent = t(`tab.${name}`);
      b.addEventListener("click", () => go(lesson, name));
      b.addEventListener("keydown", (e) => {
        const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
        if (!step) return;
        const next = TABS[(TABS.indexOf(name) + step + TABS.length) % TABS.length];
        go(lesson, next);
        requestAnimationFrame(() => $(`tab-${next}`)?.focus());
      });
      return b;
    }),
  );
}

function render() {
  const { lesson, tab } = route();
  const data = lessons.find((l) => l.id === lesson);
  document.documentElement.lang = lang();
  applyStatic();
  document.querySelectorAll("[data-lang]").forEach((b) => {
    b.setAttribute("aria-pressed", String(b.dataset.lang === lang()));
  });
  $("lesson-number").textContent = t("ui.lessonNumber", { n: lesson });
  $("lesson-title").textContent = t(`lesson.${lesson}.title`);
  $("lesson-subtitle").textContent = t(`lesson.${lesson}.subtitle`);
  document.title = `${t(`lesson.${lesson}.title`)} — gRPC Lab`;
  renderMenu(lesson);
  renderTabs(lesson, tab);
  const panel = $("panel");
  panel.setAttribute("aria-labelledby", `tab-${tab}`);
  panel.dataset.testid = `panel-${tab}`;
  panel.replaceChildren(renderTab(tab, data, { t, lang: lang(), progress, rerender: render }));
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const toggle = document.querySelector("[data-testid=theme-toggle]");
  toggle.setAttribute("aria-pressed", String(theme === "dark"));
}

async function start() {
  await loadI18n();
  lessons = await fetch(new URL("../content/lessons.json", import.meta.url)).then((r) => r.json());
  applyTheme(progress.getPref("theme", "light"));
  document.querySelectorAll("[data-lang]").forEach((b) => {
    b.addEventListener("click", () => {
      setLang(b.dataset.lang);
      render();
    });
  });
  document.querySelector("[data-testid=theme-toggle]").addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    progress.setPref("theme", next);
    applyTheme(next);
  });
  window.addEventListener("hashchange", render);
  render();
}

start();
