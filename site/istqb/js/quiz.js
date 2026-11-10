// Section quiz: 5 questions from the section's bank, rotating on every new attempt.
// After each answer the Master-Inspector explains it. Done with 4 or more right answers.

import { character } from "./art.js";
import { el } from "./dom.js";
import { pick } from "./i18n.js";
import { registerTab } from "./tabs.js";

export const QUIZ_SIZE = 5;

/** Five questions of a section; attempt n starts at question 5·n (wrapping), so retakes differ. */
export function pickQuiz(questions, sectionId, attempt = 0) {
  const pool = questions.filter((q) => q.section === sectionId).sort((a, b) => (a.id < b.id ? -1 : 1));
  if (pool.length <= QUIZ_SIZE) return pool;
  const start = (attempt * QUIZ_SIZE) % pool.length;
  return Array.from({ length: QUIZ_SIZE }, (_, i) => pool[(start + i) % pool.length]);
}

/** One question block; onAnswer(right: boolean) is called once. Used by the quiz and the exam review. */
export function questionBlock(item, n, t, onAnswer) {
  const fs = el("fieldset", { className: "quiz__q", dataset: { testid: "quiz-question" } });
  const two = item.answer.length === 2;
  fs.append(el("legend", {}, `${n}. ${pick(item.q)}${two ? ` ${t("quiz.selectTwo")}` : ""}`));
  const why = el("p", { className: "quiz__why", dataset: { testid: "quiz-why" }, hidden: true });
  const chosen = new Set();
  const options = pick(item.options);
  const buttons = options.map((text, oi) =>
    el("button", {
      type: "button",
      className: "quiz__option",
      textContent: text,
      dataset: { testid: "quiz-option", correct: String(item.answer.includes(oi)) },
    }),
  );
  const check = two ? el("button", { type: "button", className: "button", textContent: t("quiz.check"), disabled: true, dataset: { testid: "quiz-check" } }) : null;

  const reveal = () => {
    const right = chosen.size === item.answer.length && item.answer.every((a) => chosen.has(a));
    buttons.forEach((b, i) => {
      b.disabled = true;
      if (item.answer.includes(i)) b.dataset.state = "right";
      else if (chosen.has(i)) b.dataset.state = "wrong";
    });
    if (check) check.hidden = true;
    why.hidden = false;
    why.replaceChildren(el("b", {}, `${t(right ? "quiz.right" : "quiz.wrong")}. `), pick(item.why));
    onAnswer(right);
  };

  buttons.forEach((b, i) =>
    b.addEventListener("click", () => {
      if (!two) {
        chosen.add(i);
        reveal();
        return;
      }
      if (chosen.has(i)) chosen.delete(i);
      else if (chosen.size < 2) chosen.add(i);
      b.setAttribute("aria-pressed", String(chosen.has(i)));
      check.disabled = chosen.size !== 2;
    }),
  );
  check?.addEventListener("click", reveal);
  fs.append(el("div", { className: "quiz__options" }, ...buttons), check, why);
  return fs;
}

registerTab("quiz", (ctx) => {
  const { t, meta, questions, progress } = ctx;
  const attempt = progress.get().sections[meta.id]?.attempts ?? 0;
  const items = pickQuiz(questions, meta.id, attempt);
  const wrap = el("div", { className: "quiz" });
  if (!items.length) {
    wrap.append(el("p", { className: "placeholder-note" }, t("ui.comingSoon")));
    return wrap;
  }
  const answers = [];
  const score = el("div", { className: "quiz__score", dataset: { testid: "quiz-score" }, attrs: { "aria-live": "polite" } });
  const finish = () => {
    if (answers.length < items.length) return;
    const right = answers.filter(Boolean).length;
    progress.save(meta.id, right);
    ctx.refreshMenu();
    const passed = right >= 4;
    score.innerHTML = character("inspector", passed ? "happy" : "stern", t("char.inspector"));
    score.append(
      el("p", {}, el("b", {}, t("quiz.score", { n: right, total: items.length })), " ", t(passed ? "quiz.done" : "quiz.again")),
      el("button", {
        type: "button",
        className: "button button--quiet",
        textContent: t("quiz.retake"),
        dataset: { testid: "quiz-retake" },
        onclick: () => wrap.replaceWith(ctx.render("quiz")),
      }),
    );
  };
  items.forEach((item, i) => wrap.append(questionBlock(item, i + 1, t, (right) => (answers.push(right), finish()))));
  wrap.append(score);
  return wrap;
});
