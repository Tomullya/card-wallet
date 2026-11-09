// Comic strip at the top of each lesson. Panels come from content/lessons.json.

import { character } from "./art.js";
import { registerTab } from "./tabs.js";

function panelEl(panel, t) {
  const el = document.createElement("figure");
  el.className = `comic__panel comic__panel--${panel.scene}`;
  el.dataset.testid = "comic-panel";

  if (panel.caption) {
    const cap = document.createElement("figcaption");
    cap.className = "comic__caption";
    cap.textContent = t(panel.caption);
    el.append(cap);
  }

  const stage = document.createElement("div");
  stage.className = "comic__stage";
  const owls = panel.owls ?? 0;
  const flock = Array.from({ length: owls }, (_, i) =>
    `<span class="comic__owl" style="--i:${i}">${character("owl", "idle", t("char.owl"))}</span>`,
  ).join("");
  stage.innerHTML =
    flock +
    (panel.speaker && panel.speaker !== "owl"
      ? `<span class="comic__hero comic__hero--${panel.side ?? "left"}">${character(panel.speaker, panel.pose ?? "idle", t(`char.${panel.speaker}`))}</span>`
      : "");
  el.append(stage);

  if (panel.text) {
    const bubble = document.createElement("p");
    bubble.className = `comic__bubble comic__bubble--${panel.side ?? "left"}`;
    bubble.dataset.testid = "comic-bubble";
    bubble.textContent = t(panel.text);
    el.append(bubble);
  }

  if (panel.stamp) {
    const stamp = document.createElement("p");
    stamp.className = `comic__stamp comic__stamp--${panel.stamp === "OK" || panel.stamp === "APPROVE" ? "ok" : "bad"}`;
    stamp.textContent = panel.stamp;
    el.append(stamp);
  }
  return el;
}

export function renderComic(lesson, { t }) {
  const wrap = document.createElement("div");
  wrap.className = "comic";
  if (!lesson.comic?.length) {
    const note = document.createElement("p");
    note.className = "placeholder-note";
    note.textContent = t("ui.comingSoon");
    wrap.append(note);
    return wrap;
  }
  wrap.append(...lesson.comic.map((p) => panelEl(p, t)));
  return wrap;
}

registerTab("comic", renderComic);
