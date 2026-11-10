// Comic strip on each chapter page. Panels come from content/comics.json ({ru, en} texts).

import { character } from "./art.js";
import { el } from "./dom.js";
import { pick } from "./i18n.js";

function panelEl(panel, t) {
  const fig = el("figure", { className: `comic__panel comic__panel--${panel.scene}`, dataset: { testid: "comic-panel" } });
  if (panel.caption) fig.append(el("figcaption", { className: "comic__caption" }, pick(panel.caption)));
  const stage = el("div", { className: "comic__stage" });
  const owls = Array.from({ length: panel.owls ?? 0 }, (_, i) => `<span class="comic__owl" style="--i:${i}">${character("owl", "idle", t("char.owl"))}</span>`).join("");
  const hero = panel.speaker !== "owl"
    ? `<span class="comic__hero comic__hero--${panel.side}">${character(panel.speaker, panel.pose, t(`char.${panel.speaker}`))}</span>`
    : "";
  stage.innerHTML = owls + hero;
  fig.append(stage, el("p", { className: `comic__bubble comic__bubble--${panel.side}`, dataset: { testid: "comic-bubble" } }, pick(panel.text)));
  if (panel.stamp) {
    const good = ["OK", "BVA", "REVIEW"].includes(panel.stamp);
    fig.append(el("p", { className: `comic__stamp comic__stamp--${good ? "ok" : "bad"}` }, panel.stamp));
  }
  return fig;
}

export function renderComic(panels, t) {
  const wrap = el("div", { className: "comic" });
  wrap.style.setProperty("--cols", String(panels.length === 4 ? 2 : Math.min(panels.length, 3)));
  wrap.append(...panels.map((p) => panelEl(p, t)));
  return wrap;
}
