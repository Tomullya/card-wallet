// Quiz: five questions; an explanation from the Master-Inspector after each answer.
// A lesson counts as done with 4 or more correct answers.

import { character } from "./art.js";
import { registerTab } from "./tabs.js";

registerTab("quiz", (lesson, ctx) => {
  const { t } = ctx;
  const wrap = document.createElement("div");
  wrap.className = "quiz";
  if (!lesson.quiz?.length) {
    const p = document.createElement("p");
    p.className = "placeholder-note";
    p.textContent = t("ui.comingSoon");
    wrap.append(p);
    return wrap;
  }

  const answers = new Map();
  const score = document.createElement("div");
  score.className = "quiz__score";
  score.dataset.testid = "quiz-score";
  score.setAttribute("aria-live", "polite");

  const finish = () => {
    if (answers.size < lesson.quiz.length) return;
    const right = [...answers.values()].filter(Boolean).length;
    ctx.progress.save(lesson.id, right);
    ctx.refreshMenu();
    const passed = right >= 4;
    score.innerHTML = `${character("inspector", passed ? "happy" : "stern", t("char.inspector"))}
      <p><b>${t("quiz.score", { n: right, total: lesson.quiz.length })}</b> ${t(passed ? "quiz.done" : "quiz.again")}</p>`;
    const again = document.createElement("button");
    again.type = "button";
    again.className = "button button--quiet";
    again.textContent = t("quiz.retake");
    again.addEventListener("click", () => wrap.replaceWith(ctx.render("quiz")));
    score.append(again);
  };

  lesson.quiz.forEach((item, qi) => {
    const fs = document.createElement("fieldset");
    fs.className = "quiz__q";
    fs.dataset.testid = "quiz-question";
    const legend = document.createElement("legend");
    legend.textContent = `${qi + 1}. ${t(item.q)}`;
    fs.append(legend);
    const why = document.createElement("p");
    why.className = "quiz__why";
    why.dataset.testid = "quiz-why";
    why.hidden = true;
    const buttons = item.options.map((key, oi) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "quiz__option";
      b.dataset.testid = "quiz-option";
      b.textContent = t(key);
      b.addEventListener("click", () => {
        const right = oi === item.answer;
        answers.set(qi, right);
        buttons.forEach((x, xi) => {
          x.disabled = true;
          if (xi === item.answer) x.dataset.state = "right";
        });
        if (!right) b.dataset.state = "wrong";
        why.hidden = false;
        why.innerHTML = `<b>${t(right ? "quiz.right" : "quiz.wrong")}.</b> ${t(item.why)}`;
        finish();
      });
      return b;
    });
    const opts = document.createElement("div");
    opts.className = "quiz__options";
    opts.append(...buttons);
    fs.append(opts, why);
    wrap.append(fs);
  });
  wrap.append(score);
  return wrap;
});
