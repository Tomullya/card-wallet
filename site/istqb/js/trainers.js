// Trainer tab: practise a test technique on real Card Wallet rules and get instant feedback.
// Section files list their trainers, e.g. "trainers": ["ep", "bva"].

import { character } from "./art.js";
import { el, money } from "./dom.js";
import { registerTab } from "./tabs.js";
import { BOUNDARIES, PARTITIONS, bvaCheck, epCheck } from "./techniques.js";
import { RULES } from "./wallet-rules.js";

const builders = {};

/** Register a trainer: build(ctx) → element. Used by later trainers too. */
export function registerTrainer(kind, build) {
  builders[kind] = build;
}

export const splitValues = (text) =>
  String(text)
    .split(/[;\n]+/)
    .map((v) => v.trim())
    .filter(Boolean);

const pct = (n, total) => Math.round((100 * n) / total);

/** Common frame: title, task text, input, check button, result area. */
function frame(kind, t, { title, task, controls, placeholder, onCheck }) {
  const input = el("textarea", {
    className: "trainer__input",
    rows: 3,
    placeholder,
    dataset: { testid: "trainer-input" },
    attrs: { "aria-label": t("trainer.inputLabel") },
  });
  const result = el("div", { className: "trainer__result", dataset: { testid: "trainer-result" }, attrs: { "aria-live": "polite" } });
  const button = el("button", { type: "button", className: "button", textContent: t("trainer.check"), dataset: { testid: "trainer-check" } });
  button.addEventListener("click", () => result.replaceChildren(...onCheck(splitValues(input.value))));
  return el(
    "section",
    { className: "trainer", dataset: { testid: `trainer-${kind}` } },
    el("h2", {}, title),
    el("p", { className: "trainer__task" }, task),
    controls ?? null,
    el("label", { className: "trainer__label" }, t("trainer.inputLabel"), el("small", {}, t("trainer.inputHint"))),
    input,
    el("div", { className: "trainer__actions" }, button),
    result,
  );
}

function radios(name, options, testid) {
  return el(
    "div",
    { className: "trainer__radios", attrs: { role: "radiogroup" } },
    ...options.map(([value, label], i) => {
      const input = el("input", { type: "radio", name, value, checked: i === 0, dataset: { testid: `${testid}-${value}` } });
      return el("label", {}, input, " ", label);
    }),
  );
}

function verdict(t, percent, lines) {
  const happy = percent === 100;
  const face = el("div", { className: "trainer__face" });
  face.innerHTML = character("inspector", happy ? "happy" : "ask", t("char.inspector"));
  return [
    el(
      "div",
      { className: `trainer__verdict ${happy ? "trainer__verdict--ok" : ""}` },
      face,
      el("div", {}, el("p", { className: "trainer__pct" }, t("trainer.coverage", { pct: percent })), ...lines),
    ),
  ];
}

function invalidLine(t, invalid) {
  return invalid.length
    ? el("p", { className: "trainer__invalid", dataset: { testid: "trainer-invalid" } }, t("trainer.invalid", { values: invalid.join("; ") }))
    : null;
}

const PARTITION_VARS = {
  zero: "0.00",
  threshold: RULES.fraudThreshold,
  above: money(BOUNDARIES.fraud[1]),
  max: RULES.amountMax,
};

registerTrainer("ep", ({ t }) => {
  const controls = radios("ep-task", [["amount", t("ep.task.amount")], ["category", t("ep.task.category")]], "ep-task");
  const task = () => controls.querySelector("input:checked").value;
  const label = (kind, id) => t(`ep.${kind}.${id}`, PARTITION_VARS);
  return frame("ep", t, {
    title: t("ep.title"),
    task: t("ep.rules", { threshold: RULES.fraudThreshold, max: RULES.amountMax, categories: RULES.categories.join(", ") }),
    controls,
    placeholder: t("ep.placeholder"),
    onCheck(values) {
      const kind = task();
      const r = epCheck(kind, values);
      const total = PARTITIONS[kind].length;
      const percent = pct(r.covered.length, total);
      const list = el(
        "ul",
        { className: "trainer__parts" },
        ...PARTITIONS[kind].map((p) =>
          el(
            "li",
            { dataset: { state: r.covered.includes(p.id) ? "covered" : "missing" } },
            `${r.covered.includes(p.id) ? "✓" : "✗"} ${label(kind, p.id)} — ${t(p.valid ? "ep.valid" : "ep.invalid")}`,
          ),
        ),
      );
      return verdict(t, percent, [
        el("p", {}, t("trainer.items", { n: r.covered.length, total })),
        list,
        r.missing.length
          ? el("p", { dataset: { testid: "missing" } }, t("ep.missing", { parts: r.missing.map((id) => label(kind, id)).join("; ") }))
          : null,
        r.duplicates.length
          ? el("p", { className: "trainer__note" }, t("ep.duplicates", { values: r.duplicates.map(([v, id]) => `${v} (${label(kind, id)})`).join("; ") }))
          : null,
        invalidLine(t, r.invalid),
      ]);
    },
  });
});

registerTrainer("bva", ({ t }) => {
  const taskControls = radios("bva-task", [["fraud", t("bva.task.fraud")], ["amount", t("bva.task.amount")]], "bva-task");
  const variantControls = radios("bva-variant", [["2", t("bva.variant2")], ["3", t("bva.variant3")]], "bva-variant");
  const controls = el("div", { className: "trainer__controls" }, taskControls, variantControls);
  return frame("bva", t, {
    title: t("bva.title"),
    task: t("bva.rules", { threshold: RULES.fraudThreshold, min: RULES.amountMin, max: RULES.amountMax }),
    controls,
    placeholder: t("bva.placeholder"),
    onCheck(values) {
      const kind = taskControls.querySelector("input:checked").value;
      const variant = Number(variantControls.querySelector("input:checked").value);
      const r = bvaCheck(kind, values, variant);
      const percent = pct(r.covered.length, r.required.length);
      return verdict(t, percent, [
        el("p", {}, t("trainer.items", { n: r.covered.length, total: r.required.length })),
        el("p", {}, t("bva.required", { values: r.required.map(money).join("; ") })),
        r.missing.length ? el("p", { dataset: { testid: "missing" } }, t("bva.missing", { values: r.missing.map(money).join("; ") })) : null,
        r.extra.length ? el("p", { className: "trainer__note" }, t("bva.extra", { values: r.extra.map(money).join("; ") })) : null,
        invalidLine(t, r.invalid),
      ]);
    },
  });
});

registerTab("trainer", (ctx) => {
  const wrap = el("div", { className: "trainers" });
  wrap.append(el("p", { className: "trainers__lead" }, ctx.t("trainer.lead")));
  ctx.section.trainers.forEach((kind) => builders[kind] && wrap.append(builders[kind](ctx)));
  return wrap;
});
