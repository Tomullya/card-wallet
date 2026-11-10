// Shell: chapter menu, routing, language and theme switches.
// Routes: #/ (home), #/ch/<n>, #/s/<section>/<tab>, #/glossary, #/exam.

import { applyStatic, lang, loadI18n, pick, setLang, t } from "./i18n.js";
import * as progress from "./progress.js";
import { renderPage, renderTab } from "./tabs.js";
import "./pages.js";
import "./theory.js";
import "./terms.js";
import "./quiz.js";
import "./trainers.js";

export const BASE_TABS = ["theory", "terms", "quiz"];
let syllabus = null;
let questions = [];
const sectionCache = new Map();
let renderId = 0;

const $ = (id) => document.getElementById(id);

const allSections = () => syllabus.chapters.flatMap((c) => c.sections.map((s) => ({ ...s, chapter: c })));

/** Content of one section, or null when it is not written yet. */
export async function loadSection(id) {
  if (!sectionCache.has(id)) {
    const url = new URL(`../content/sections/${id}.json`, import.meta.url);
    sectionCache.set(id, fetch(url).then((r) => (r.ok ? r.json() : null)).catch(() => null));
  }
  return sectionCache.get(id);
}

function tabsFor(section) {
  return section?.trainers?.length ? [...BASE_TABS, "trainer"] : BASE_TABS;
}

function route() {
  const hash = location.hash;
  let m = hash.match(/^#\/ch\/([1-6])$/);
  if (m) return { page: "chapter", chapter: m[1] };
  m = hash.match(/^#\/s\/(\d\.\d)\/(\w+)$/);
  if (m && allSections().some((s) => s.id === m[1])) return { page: "section", section: m[1], tab: m[2] };
  if (hash === "#/glossary") return { page: "glossary" };
  if (hash === "#/exam") return { page: "exam" };
  return { page: "home" };
}

function go(target, { focus } = {}) {
  if (location.hash !== target) history.pushState(null, "", target);
  render().then(() => focus && $(focus)?.focus());
}

function link(href, testid, className, children) {
  const a = document.createElement("a");
  a.href = href;
  a.dataset.testid = testid;
  a.className = className;
  a.append(...children);
  return a;
}

function span(className, text) {
  const s = document.createElement("span");
  s.className = className;
  s.textContent = text;
  return s;
}

function renderMenu(current) {
  const done = progress.get().sections;
  $("chapter-list").replaceChildren(
    ...syllabus.chapters.map((c) => {
      const li = document.createElement("li");
      const head = link(`#/ch/${c.id}`, `chapter-${c.id}`, "chapters__link", [
        span("chapters__num", c.id),
        span("chapters__name", pick(c.title)),
      ]);
      if (current.page === "chapter" && current.chapter === c.id) head.setAttribute("aria-current", "page");
      const ol = document.createElement("ol");
      ol.className = "chapters__sections";
      ol.append(
        ...c.sections.map((s) => {
          const item = document.createElement("li");
          const a = link(`#/s/${s.id}/theory`, `section-${s.id}`, "sections__link", [
            span("sections__num", s.id),
            span("sections__name", pick(s.title)),
          ]);
          if (current.section === s.id) a.setAttribute("aria-current", "page");
          if (done[s.id]?.done) {
            const mark = span("sections__done", "✓");
            mark.dataset.testid = `done-${s.id}`;
            mark.setAttribute("aria-label", t("ui.done"));
            a.append(mark);
          }
          item.append(a);
          return item;
        }),
      );
      li.append(head, ol);
      return li;
    }),
  );
  const count = Object.values(done).filter((x) => x.done).length;
  $("progress-note").textContent = t("ui.progress", { n: count, total: allSections().length });
}

function renderTabs(sectionId, names, current) {
  const list = $("tab-list");
  list.hidden = !names.length;
  list.replaceChildren(
    ...names.map((name) => {
      const b = document.createElement("button");
      b.type = "button";
      b.role = "tab";
      b.id = `tab-${name}`;
      b.dataset.testid = `tab-${name}`;
      b.setAttribute("aria-selected", String(name === current));
      b.setAttribute("aria-controls", "panel");
      b.tabIndex = name === current ? 0 : -1;
      b.textContent = t(`tab.${name}`);
      b.addEventListener("click", () => go(`#/s/${sectionId}/${name}`));
      b.addEventListener("keydown", (e) => {
        const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
        if (!step) return;
        const next = names[(names.indexOf(name) + step + names.length) % names.length];
        go(`#/s/${sectionId}/${next}`, { focus: `tab-${next}` });
      });
      return b;
    }),
  );
}

function setHead(kicker, title, subtitle) {
  $("page-kicker").textContent = kicker;
  $("page-title").textContent = title;
  $("page-subtitle").textContent = subtitle;
  document.title = `${title} — ISTQB Lab`;
}

async function render() {
  const id = ++renderId;
  const r = route();
  const ctx = {
    t,
    lang: lang(),
    progress,
    syllabus,
    questions,
    go,
    rerender: render,
    refreshMenu: () => renderMenu(r),
  };
  let section = null;
  if (r.page === "section") section = await loadSection(r.section);
  if (id !== renderId) return; // a newer render started while loading

  document.documentElement.lang = lang();
  applyStatic();
  document.querySelectorAll("[data-lang]").forEach((b) => {
    b.setAttribute("aria-pressed", String(b.dataset.lang === lang()));
  });
  $("disclaimer").textContent = t("ui.disclaimer");
  $("syllabus-note").textContent = t("ui.syllabusNote", { version: syllabus.version });
  renderMenu(r);
  const panel = $("panel");

  if (r.page === "section") {
    const meta = allSections().find((s) => s.id === r.section);
    const names = tabsFor(section);
    const tab = names.includes(r.tab) ? r.tab : "theory";
    Object.assign(ctx, { section, meta, chapter: meta.chapter, render: (name) => renderTab(name, ctx) });
    setHead(
      t("ui.sectionKicker", { id: meta.id, chapter: meta.chapter.id }),
      `${meta.id} ${pick(meta.title)}`,
      pick(meta.chapter.title),
    );
    renderTabs(meta.id, names, tab);
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", `tab-${tab}`);
    panel.dataset.testid = `panel-${tab}`;
    panel.replaceChildren(renderTab(tab, ctx));
    return;
  }

  renderTabs(null, [], null);
  panel.removeAttribute("role");
  panel.removeAttribute("aria-labelledby");
  panel.dataset.testid = `page-${r.page}`;
  if (r.page === "chapter") {
    const chapter = syllabus.chapters.find((c) => c.id === r.chapter);
    Object.assign(ctx, { chapter });
    setHead(t("ui.chapterKicker", { id: chapter.id }), pick(chapter.title), t("ui.minutes", { n: chapter.minutes }));
  } else {
    setHead(t(`page.${r.page}.kicker`), t(`page.${r.page}.title`), t(`page.${r.page}.subtitle`));
  }
  const node = await Promise.resolve(renderPage(r.page, ctx));
  if (id === renderId) panel.replaceChildren(node); // skip if the reader already moved on
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.querySelector("[data-testid=theme-toggle]").setAttribute("aria-pressed", String(theme === "dark"));
}

async function start() {
  await loadI18n();
  [syllabus, questions] = await Promise.all(
    ["syllabus", "questions"].map((name) =>
      fetch(new URL(`../content/${name}.json`, import.meta.url)).then((r) => r.json()),
    ),
  );
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
  window.addEventListener("popstate", render);
  document.querySelector(".skip").addEventListener("click", (e) => {
    e.preventDefault(); // "#main" is not a route: stay on the page, just move focus
    $("main").focus();
  });
  render();
}

start();
