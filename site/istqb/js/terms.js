// Terms tab: the section's key terms in both languages with a short own explanation.

import { el } from "./dom.js";
import { pick, term } from "./i18n.js";
import { registerTab } from "./tabs.js";

registerTab("terms", ({ t, section, syllabus }) => {
  const list = el("dl", { className: "terms" });
  section.terms.forEach((x) => {
    list.append(
      el(
        "div",
        { className: "terms__item", dataset: { testid: "term" } },
        el("dt", { dataset: { testid: "term-name" } }, term(x)),
        el("dd", {}, pick(x.explain)),
      ),
    );
  });
  return el(
    "div",
    {},
    list,
    el(
      "p",
      { className: "terms__more" },
      t("terms.more"),
      " ",
      el("a", { href: syllabus.links.glossary, target: "_blank", rel: "noopener" }, "glossary.istqb.org"),
    ),
  );
});
