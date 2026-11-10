// Home (map of chapters) and chapter pages.

import { renderComic } from "./comic.js";
import { pick } from "./i18n.js";
import { registerPage } from "./tabs.js";

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function doneCount(chapter, progress) {
  const done = progress.get().sections;
  return chapter.sections.filter((s) => done[s.id]?.done).length;
}

registerPage("home", ({ t, syllabus, progress }) => {
  const wrap = el("div", "home");
  wrap.append(el("p", "home__lead", t("home.lead")));
  const grid = el("ol", "map");
  syllabus.chapters.forEach((c) => {
    const li = document.createElement("li");
    const a = el("a", "map__card");
    a.href = `#/ch/${c.id}`;
    a.dataset.testid = "chapter-card";
    const n = doneCount(c, progress);
    a.append(
      el("span", "map__num", c.id),
      el("span", "map__title", pick(c.title)),
      el("span", "map__meta", t("home.cardMeta", { done: n, total: c.sections.length, minutes: c.minutes })),
    );
    const bar = el("span", "map__bar");
    bar.style.setProperty("--done", `${(100 * n) / c.sections.length}%`);
    a.append(bar);
    li.append(a);
    grid.append(li);
  });
  wrap.append(grid, el("p", "home__how", t("home.how")));
  return wrap;
});

let comics = null;

registerPage("chapter", async (ctx) => {
  const { t, chapter, progress } = ctx;
  comics ??= await fetch(new URL("../content/comics.json", import.meta.url)).then((r) => r.json());
  const wrap = el("div", "chapter");
  wrap.dataset.testid = "chapter-page";
  if (comics[chapter.id]) wrap.append(renderComic(comics[chapter.id], t));
  wrap.append(el("h2", "chapter__h", t("chapter.sections")));
  const done = progress.get().sections;
  const list = el("ol", "chapter__sections");
  chapter.sections.forEach((s) => {
    const li = document.createElement("li");
    const a = el("a", "chapter__section");
    a.href = `#/s/${s.id}/theory`;
    a.dataset.testid = "chapter-section";
    a.append(
      el("span", "chapter__num", s.id),
      el("span", "chapter__name", pick(s.title)),
      el("span", "chapter__meta", t("chapter.objectives", { n: s.los.length })),
    );
    if (done[s.id]?.done) a.append(el("span", "sections__done", "✓"));
    li.append(a);
    list.append(li);
  });
  wrap.append(list);
  return wrap;
});
