// Glossary page: all terms of all written sections, RU and EN side by side, with search.

import { el } from "./dom.js";
import { pick, term } from "./i18n.js";
import { registerPage } from "./tabs.js";

registerPage("glossary", async ({ t, lang, syllabus, loadSection }) => {
  const ids = syllabus.chapters.flatMap((c) => c.sections.map((s) => s.id));
  const sections = (await Promise.all(ids.map(loadSection))).filter(Boolean);
  const seen = new Map();
  for (const s of sections) {
    for (const x of s.terms) {
      const key = x.en.toLowerCase();
      if (!seen.has(key)) seen.set(key, { ...x, sections: [] });
      seen.get(key).sections.push(s.id);
    }
  }
  const terms = [...seen.values()].sort((a, b) => a[lang].localeCompare(b[lang], lang));
  const items = terms.map((x) =>
    el(
      "div",
      { className: "terms__item", dataset: { testid: "glossary-term", search: `${x.ru} ${x.en}`.toLowerCase() } },
      el("dt", {}, term(x)),
      el("dd", {}, pick(x.explain), " ", ...x.sections.map((id) => el("a", { href: `#/s/${id}/terms`, className: "glossary__ref" }, `§${id}`))),
    ),
  );
  const empty = el("p", { className: "placeholder-note", hidden: true }, t("glossary.empty"));
  const search = el("input", {
    type: "search",
    className: "glossary__search",
    placeholder: t("glossary.search"),
    dataset: { testid: "glossary-search" },
    attrs: { "aria-label": t("glossary.search") },
  });
  search.addEventListener("input", () => {
    const needle = search.value.trim().toLowerCase();
    let shown = 0;
    items.forEach((item) => {
      item.hidden = Boolean(needle) && !item.dataset.search.includes(needle);
      if (!item.hidden) shown += 1;
    });
    empty.hidden = shown > 0;
  });
  return el(
    "div",
    { className: "glossary" },
    el("p", {}, t("glossary.lead", { n: terms.length }), " ", el("a", { href: syllabus.links.glossary, target: "_blank", rel: "noopener" }, "glossary.istqb.org")),
    search,
    el("dl", { className: "terms" }, ...items),
    empty,
  );
});
