// Theory and practice tabs. Lesson texts are our own trusted content with simple <b>/<code> markup.

import { registerTab } from "./tabs.js";

const REPO = "https://github.com/Tomullya/card-wallet/blob/main/";

function comingSoon(t) {
  const p = document.createElement("p");
  p.className = "placeholder-note";
  p.textContent = t("ui.comingSoon");
  return p;
}

registerTab("theory", (lesson, { t }) => {
  if (!lesson.theory) return comingSoon(t);
  const article = document.createElement("article");
  article.className = "theory";
  for (let i = 1; i <= lesson.theory; i++) {
    const p = document.createElement("p");
    p.innerHTML = t(`l${lesson.id}.theory.${i}`);
    article.append(p);
  }
  return article;
});

registerTab("practice", (lesson, { t }) => {
  const wrap = document.createElement("div");
  wrap.className = "practice";

  if (lesson.postman) {
    const h = document.createElement("h2");
    h.textContent = t("pr.postman");
    const ol = document.createElement("ol");
    for (let i = 1; i <= lesson.postman; i++) {
      const li = document.createElement("li");
      li.innerHTML = t(`l${lesson.id}.postman.${i}`);
      ol.append(li);
    }
    wrap.append(h, ol);
  }

  const h2 = document.createElement("h2");
  h2.textContent = t("pr.check");
  wrap.append(h2);
  if (lesson.practice?.check) {
    const hint = document.createElement("p");
    hint.textContent = t("pr.checkHint");
    const pre = document.createElement("pre");
    pre.className = "command";
    pre.dataset.testid = "practice-check";
    pre.textContent = `.venv/bin/python scripts/grpc_lab_check.py ${lesson.practice.check}`;
    wrap.append(hint, pre);
  } else {
    const p = document.createElement("p");
    p.textContent = t("pr.noCheck");
    wrap.append(p);
  }

  const h3 = document.createElement("h2");
  h3.textContent = t("pr.files");
  const ul = document.createElement("ul");
  ul.className = "files";
  for (const path of lesson.practice?.files ?? []) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = REPO + path;
    a.target = "_blank";
    a.rel = "noopener";
    a.dataset.testid = "practice-link";
    a.textContent = path;
    li.append(a);
    ul.append(li);
  }
  wrap.append(h3, ul);
  return wrap;
});
