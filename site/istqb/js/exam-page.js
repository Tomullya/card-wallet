// Mock exam page: start screen → 40 questions with a timer → results per chapter and review.
// The exam state lives in progress storage, so a reload or a language switch keeps it.

import { character } from "./art.js";
import { el } from "./dom.js";
import {
  DISTRIBUTION,
  MINUTES,
  MINUTES_EXTENDED,
  PASS_MARK,
  answer,
  isRight,
  remaining,
  resume,
  startExam,
  submit,
} from "./exam.js";
import { pick } from "./i18n.js";
import { questionBlock } from "./quiz.js";
import { registerPage } from "./tabs.js";

let ticker = null;

const clock = (seconds) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;

function samples(t, syllabus) {
  return el(
    "section",
    { className: "exam__samples" },
    el("h2", {}, t("exam.samplesTitle")),
    el("p", {}, t("exam.samplesLead")),
    el(
      "ul",
      {},
      ...syllabus.links.samples.map((s) =>
        el(
          "li",
          {},
          t("exam.sample", { name: s.name }),
          " — ",
          el("a", { href: s.en, target: "_blank", rel: "noopener", dataset: { testid: "sample-link" } }, "EN"),
          s.ru ? " · " : "",
          s.ru ? el("a", { href: s.ru, target: "_blank", rel: "noopener", dataset: { testid: "sample-link" } }, "RU") : "",
        ),
      ),
    ),
    el("p", {}, el("a", { href: syllabus.links.official, target: "_blank", rel: "noopener" }, t("exam.official"))),
  );
}

function startScreen(ctx) {
  const { t, questions, progress, syllabus } = ctx;
  const wrap = el("div", { className: "exam" });
  wrap.append(el("p", {}, t("exam.lead", { pass: PASS_MARK })));
  const chapters = Object.entries(DISTRIBUTION).map(([ch, n]) => t("exam.chapterCount", { ch, n })).join(" · ");
  wrap.append(el("p", { className: "trainer__note" }, chapters));
  const long = el("input", { type: "checkbox", dataset: { testid: "exam-extended" } });
  wrap.append(el("label", { className: "exam__extended" }, long, " ", t("exam.extended", { minutes: MINUTES_EXTENDED })));
  const error = el("p", { className: "trainer__invalid", hidden: true, dataset: { testid: "exam-error" } });
  const start = el("button", { type: "button", className: "button", textContent: t("exam.start"), dataset: { testid: "exam-start" } });
  start.addEventListener("click", () => {
    try {
      const state = startExam(questions, {
        seed: Math.floor(Math.random() * 2 ** 31),
        now: Date.now(),
        minutes: long.checked ? MINUTES_EXTENDED : MINUTES,
      });
      progress.setExam(state);
      ctx.rerender();
    } catch (e) {
      error.hidden = false;
      error.textContent = t("exam.bankTooSmall", { details: e.message });
    }
  });
  wrap.append(el("div", { className: "trainer__actions" }, start), error, samples(t, syllabus));
  return wrap;
}

function inProgress(ctx, state) {
  const { t, questions, progress } = ctx;
  const byId = new Map(questions.map((q) => [q.id, q]));
  const timer = el("span", { className: "exam__timer", dataset: { testid: "exam-timer" } });
  const answered = el("span", { dataset: { testid: "exam-answered" } });
  const countAnswered = () => Object.values(progress.getExam().answers).filter((a) => a.length).length;
  const showAnswered = () => (answered.textContent = t("exam.answered", { n: countAnswered(), total: state.ids.length }));
  showAnswered();

  const list = el("ol", { className: "exam__list" });
  state.ids.forEach((id, n) => {
    const q = byId.get(id);
    const two = q.answer.length === 2;
    const chosen = new Set(state.answers[id] ?? []);
    const inputs = pick(q.options).map((text, i) => {
      const input = el("input", { type: two ? "checkbox" : "radio", name: `exam-${id}`, value: String(i), checked: chosen.has(i) });
      input.addEventListener("change", () => {
        const picked = [...list.querySelectorAll(`input[name="exam-${id}"]:checked`)].map((x) => Number(x.value));
        if (two && picked.length > 2) {
          input.checked = false;
          return;
        }
        progress.setExam(answer(progress.getExam(), id, picked));
        showAnswered();
      });
      return el("label", { className: "exam__option" }, input, " ", text);
    });
    list.append(
      el(
        "li",
        { className: "quiz__q", dataset: { testid: "exam-question" } },
        el("p", { className: "exam__stem" }, el("b", {}, `${n + 1}. `), pick(q.q), two ? ` ${t("quiz.selectTwo")}` : ""),
        el("div", { className: "exam__options", attrs: { role: two ? "group" : "radiogroup" } }, ...inputs),
      ),
    );
  });

  const finish = () => {
    clearInterval(ticker);
    progress.setExam(submit(progress.getExam(), questions, Date.now()));
    ctx.rerender();
  };
  const confirm = el("div", { className: "exam__confirm", hidden: true });
  confirm.append(
    el("p", {}, t("exam.confirmText")),
    el("button", { type: "button", className: "button", textContent: t("exam.confirm"), dataset: { testid: "exam-confirm" }, onclick: finish }),
    " ",
    el("button", { type: "button", className: "button button--quiet", textContent: t("exam.cancel"), onclick: () => (confirm.hidden = true) }),
  );
  const submitButton = el("button", {
    type: "button",
    className: "button",
    textContent: t("exam.submit"),
    dataset: { testid: "exam-submit" },
    onclick: () => (confirm.hidden = false),
  });

  const tick = () => {
    if (!timer.isConnected) return clearInterval(ticker);
    const left = remaining(progress.getExam(), Date.now());
    timer.textContent = clock(left);
    timer.dataset.low = String(left < 5 * 60);
    if (left === 0) finish();
  };
  clearInterval(ticker);
  ticker = setInterval(tick, 1000);
  timer.textContent = clock(remaining(state, Date.now())); // first value now; tick() needs the page attached

  return el(
    "div",
    { className: "exam" },
    el("div", { className: "exam__bar" }, el("span", {}, "⏳ ", timer), answered, submitButton),
    list,
    el("div", { className: "trainer__actions" }, confirm),
  );
}

function results(ctx, state) {
  const { t, questions, progress, syllabus } = ctx;
  const byId = new Map(questions.map((q) => [q.id, q]));
  const r = state.result;
  const face = el("div", { className: "trainer__face" });
  face.innerHTML = character("inspector", r.passed ? "happy" : "stern", t("char.inspector"));
  const rows = Object.entries(r.byChapter).map(([ch, x]) =>
    el(
      "tr",
      { dataset: { testid: "exam-chapter-row" } },
      el("th", { scope: "row" }, `${ch}. ${pick(syllabus.chapters.find((c) => c.id === ch).title)}`),
      el("td", {}, `${x.right} / ${x.of}`),
    ),
  );
  const wrong = state.ids.filter((id) => !isRight(byId.get(id), state.answers[id]));
  const review = wrong.map((id, i) => {
    const q = byId.get(id);
    const block = el("div", { className: "exam__review", dataset: { testid: "exam-review-item" } });
    const chosen = state.answers[id] ?? [];
    block.append(
      el("p", { className: "exam__stem" }, el("b", {}, `${i + 1}. `), pick(q.q)),
      el(
        "ul",
        { className: "exam__answers" },
        ...pick(q.options).map((text, oi) =>
          el("li", { dataset: { state: q.answer.includes(oi) ? "right" : chosen.includes(oi) ? "wrong" : "" } }, text),
        ),
      ),
      el("p", { className: "quiz__why", dataset: { testid: "quiz-why" } }, el("b", {}, `${t(chosen.length ? "quiz.wrong" : "exam.unanswered")}. `), pick(q.why)),
      el("p", {}, el("a", { href: `#/s/${q.section}/theory` }, t("exam.reread", { id: q.section }))),
    );
    return block;
  });
  const retry = el("div", { className: "quiz", hidden: true });
  const retryButton = el("button", {
    type: "button",
    className: "button button--quiet",
    textContent: t("exam.retryWrong", { n: wrong.length }),
    dataset: { testid: "exam-retry-wrong" },
    hidden: !wrong.length,
    onclick: () => {
      retry.replaceChildren(...wrong.map((id, i) => questionBlock(byId.get(id), i + 1, t, () => {})));
      retry.hidden = false;
      retry.scrollIntoView({ behavior: "smooth" });
    },
  });
  const again = el("button", {
    type: "button",
    className: "button",
    textContent: t("exam.again"),
    dataset: { testid: "exam-new" },
    onclick: () => (progress.setExam(null), ctx.rerender()),
  });
  return el(
    "div",
    { className: "exam" },
    el(
      "div",
      { className: `trainer__verdict ${r.passed ? "trainer__verdict--ok" : ""}` },
      face,
      el(
        "div",
        {},
        el("p", { className: "trainer__pct", dataset: { testid: "exam-score" } }, `${r.total} / ${r.of}`),
        el("p", {}, t(r.passed ? "exam.passed" : "exam.failed", { pass: PASS_MARK })),
      ),
    ),
    el("table", { className: "dt exam__table" }, el("tbody", {}, ...rows)),
    el("div", { className: "trainer__actions" }, again, " ", retryButton),
    wrong.length ? el("h2", {}, t("exam.reviewTitle")) : null,
    ...review,
    retry,
  );
}

registerPage("exam", (ctx) => {
  const saved = ctx.progress.getExam();
  if (!saved) return startScreen(ctx);
  const known = new Set(ctx.questions.map((q) => q.id));
  if (!saved.ids.every((id) => known.has(id))) {
    ctx.progress.setExam(null); // the bank changed since this exam was saved
    return startScreen(ctx);
  }
  const state = resume(saved, ctx.questions, Date.now());
  if (state !== saved) ctx.progress.setExam(state);
  return state.submitted ? results(ctx, state) : inProgress(ctx, state);
});
