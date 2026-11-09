// Animated owl-post diagram for the lesson's call type: who sends what, in which order.

import { character } from "./art.js";
import { registerTab } from "./tabs.js";

// dir: "out" = client → service, "in" = service → client.
const FLOWS = {
  unary: ["out", "in"],
  server: ["out", "in", "in", "in"],
  client: ["out", "out", "out", "out", "in"],
  bidi: ["out", "in", "out", "in", "out", "in"],
};
const CLIENT_OF = { unary: "treasurer", server: "watcher", client: "treasurer", bidi: "treasurer" };

const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function play(rows) {
  if (reduceMotion()) return; // final state is the default CSS state
  rows.forEach((row, i) => {
    const owl = row.querySelector(".flow__owl");
    const out = row.dataset.dir === "out";
    row.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 250, delay: i * 700, fill: "backwards" });
    owl.animate(
      [{ left: out ? "0%" : "calc(100% - 44px)" }, { left: out ? "calc(100% - 44px)" : "0%" }],
      { duration: 650, delay: i * 700, easing: "ease-in-out", fill: "backwards" },
    );
  });
}

function flowFor(type, t) {
  const wrap = document.createElement("div");
  wrap.className = "flow";
  const client = CLIENT_OF[type];
  wrap.innerHTML = `
    <p class="flow__lead">${t(`diagram.${type}.lead`)}</p>
    <div class="flow__actors">
      <div class="flow__actor">${character(client, "ask", t(`char.${client}`))}<span>${t(`char.${client}`)}</span></div>
      <div class="flow__actor">${character("inspector", "stern", t("char.inspector"))}<span>${t("char.inspector")}</span></div>
    </div>`;
  const list = document.createElement("ol");
  list.className = "flow__steps";
  const rows = FLOWS[type].map((dir, i) => {
    const li = document.createElement("li");
    li.className = `flow__step flow__step--${dir}`;
    li.dataset.testid = "diagram-step";
    li.dataset.dir = dir;
    li.innerHTML = `
      <span class="flow__track"><span class="flow__owl">${character("owl", "idle", t("char.owl"))}</span></span>
      <span class="flow__label">${t(`diagram.${type}.${i + 1}`)}</span>`;
    return li;
  });
  list.append(...rows);
  const replay = document.createElement("button");
  replay.type = "button";
  replay.className = "button button--quiet";
  replay.dataset.testid = "diagram-replay";
  replay.textContent = t("diagram.replay");
  replay.addEventListener("click", () => play(rows));
  wrap.append(list, replay);
  requestAnimationFrame(() => play(rows));
  return wrap;
}

export function renderDiagram(lesson, { t }) {
  if (lesson.diagram === "all") {
    const all = document.createElement("div");
    all.className = "flow-all";
    for (const type of Object.keys(FLOWS)) {
      const h = document.createElement("h2");
      h.className = "flow-all__title";
      h.textContent = t(`diagram.${type}.title`);
      all.append(h, flowFor(type, t));
    }
    return all;
  }
  const type = lesson.callType;
  if (!type) {
    const note = document.createElement("p");
    note.className = "placeholder-note";
    note.textContent = t("ui.comingSoon");
    return note;
  }
  return flowFor(type, t);
}

registerTab("diagram", renderDiagram);
