// Theory tab: per learning objective — quoted objective with K-level, own explanation,
// a Card Wallet example; links to the section in the official syllabus PDFs.

import { el } from "./dom.js";
import { pick } from "./i18n.js";
import { registerTab } from "./tabs.js";

registerTab("theory", ({ t, lang, section, meta, syllabus }) => {
  const wrap = el("div", { className: "theory" });
  section.objectives.forEach((o) => {
    const lo = meta.los.find((x) => x.id === o.lo);
    const ref = lo.id.slice(3);
    const card = el(
      "article",
      { className: "objective", dataset: { testid: "objective" } },
      el(
        "header",
        { className: "objective__head" },
        el("span", { className: "objective__k", dataset: { testid: "lo-badge" }, title: t(`k.${lo.k}`) }, lo.k),
        el("span", { className: "objective__id" }, lo.id),
      ),
      el(
        "blockquote",
        { className: "objective__quote" },
        el("p", { dataset: { testid: "lo-quote" } }, t("theory.quoted", { text: pick(lo.quote) })),
        el("footer", { dataset: { testid: "lo-source" } }, t("theory.source", { ref })),
      ),
      ...o.explain[lang].map((p) => el("p", {}, p)),
      el(
        "aside",
        { className: "wallet", dataset: { testid: "wallet-example" } },
        el("h3", { className: "wallet__title" }, t("theory.wallet")),
        el("p", {}, pick(o.wallet)),
        o.wallet.link ? el("a", { href: o.wallet.link, target: "_blank", rel: "noopener" }, t("theory.walletLink")) : null,
      ),
    );
    wrap.append(card);
  });
  const read = el(
    "section",
    { className: "theory__sources" },
    el("h2", {}, t("theory.read", { id: meta.id })),
    el(
      "p",
      {},
      el(
        "a",
        { href: `${syllabus.links.en}#page=${meta.pages.en}`, target: "_blank", rel: "noopener", dataset: { testid: "syllabus-link" } },
        t("theory.pdfEn", { page: meta.pages.en }),
      ),
      " · ",
      el(
        "a",
        { href: `${syllabus.links.ru}#page=${meta.pages.ru}`, target: "_blank", rel: "noopener", dataset: { testid: "syllabus-link" } },
        t("theory.pdfRu", { page: meta.pages.ru }),
      ),
    ),
  );
  wrap.append(read);
  return wrap;
});
