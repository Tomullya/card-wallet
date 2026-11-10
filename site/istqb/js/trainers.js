// Trainer tab: practise a test technique on real Card Wallet rules and get instant feedback.
// Section files list their trainers, e.g. "trainers": ["ep", "bva"].

import { character } from "./art.js";
import { el, money } from "./dom.js";
import { registerTab } from "./tabs.js";
import { BOUNDARIES, PARTITIONS, bvaCheck, codeTrace, decisionTable, epCheck, parseAmount, stateCoverage } from "./techniques.js";
import { PROGRAMS, RULES, cardEvents, cardTransitions } from "./wallet-rules.js";

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

const ACTIONS = ["APPROVE", "DECLINE_HIGH", "DECLINE_CATEGORY"];
const tf = (b) => (b === null ? "–" : b ? "T" : "F");

registerTrainer("decision", ({ t }) => {
  const combos = decisionTable([]).columns.map((c) => c.c);
  const selects = combos.map(() =>
    el(
      "select",
      { dataset: { testid: "dt-action" }, attrs: { "aria-label": t("dt.action") } },
      el("option", { value: "" }, t("dt.choose")),
      ...ACTIONS.map((a) => el("option", { value: a }, t(`dt.${a}`))),
    ),
  );
  const head = el("tr", {}, el("th", {}, ""), ...combos.map((_, i) => el("th", { scope: "col" }, t("dt.rule", { n: i + 1 }))));
  const row = (label, cells) => el("tr", {}, el("th", { scope: "row" }, label), ...cells.map((c) => el("td", {}, c)));
  const table = el(
    "table",
    { className: "dt" },
    el("thead", {}, head),
    el(
      "tbody",
      {},
      row(t("dt.c1", { threshold: RULES.fraudThreshold }), combos.map((c) => tf(c[0]))),
      row(t("dt.c2"), combos.map((c) => tf(c[1]))),
      row(t("dt.actionRow"), selects),
    ),
  );
  const result = el("div", { className: "trainer__result", dataset: { testid: "trainer-result" }, attrs: { "aria-live": "polite" } });
  const button = el("button", { type: "button", className: "button", textContent: t("trainer.check"), dataset: { testid: "trainer-check" } });
  button.addEventListener("click", () => {
    const cols = combos.map((c, i) => ({ c, action: selects[i].value })).filter((x) => x.action);
    const r = decisionTable(cols);
    const label = (c) => `(${tf(c[0])}, ${tf(c[1])})`;
    const minimised = el(
      "table",
      { className: "dt dt--small", dataset: { testid: "dt-minimised" } },
      el("tbody", {},
        row(t("dt.c1", { threshold: RULES.fraudThreshold }), r.minimised.map((m) => tf(m.c[0]))),
        row(t("dt.c2"), r.minimised.map((m) => tf(m.c[1]))),
        row(t("dt.actionRow"), r.minimised.map((m) => t(`dt.${m.action}`))),
      ),
    );
    const exercised = cols.length - r.wrong.length;
    result.replaceChildren(
      ...verdict(t, pct(exercised, 4), [
        el("p", {}, t("dt.columns", { n: exercised, total: 4 })),
        r.missing.length ? el("p", { dataset: { testid: "missing" } }, t("dt.missing", { cols: r.missing.map(label).join(", ") })) : null,
        r.wrong.length ? el("p", { className: "trainer__invalid", dataset: { testid: "dt-wrong" } }, t("dt.wrong", { cols: r.wrong.map(label).join(", ") })) : null,
        el("p", {}, t("dt.minimisedLead")),
        minimised,
      ]),
    );
  });
  return el(
    "section",
    { className: "trainer", dataset: { testid: "trainer-decision" } },
    el("h2", {}, t("dt.title")),
    el("p", { className: "trainer__task" }, t("dt.rules", { threshold: RULES.fraudThreshold })),
    el("div", { className: "dt-wrap" }, table),
    el("div", { className: "trainer__actions" }, button),
    result,
  );
});

/** Card statuses as a small diagram: three boxes, arrows labelled with events. */
function stateDiagram(t, used) {
  const box = (x, y, name) =>
    `<g><rect x="${x}" y="${y}" width="120" height="44" rx="12" fill="var(--paper)" stroke="var(--ink)" stroke-width="2.5"/><text x="${x + 60}" y="${y + 28}" text-anchor="middle" font-weight="700" fill="var(--ink)" font-family="var(--font-mono)" font-size="15">${name}</text></g>`;
  const arrow = (i, d, lx, ly, label) => {
    const on = used.includes(i);
    const color = on ? "var(--rune-ok)" : "var(--ink-soft)";
    return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${on ? 3.5 : 2}" marker-end="url(#arrow-${on ? "on" : "off"})"/><text x="${lx}" y="${ly}" font-size="12.5" fill="${color}" font-family="var(--font-body)">${label}</text>`;
  };
  const label = (i) => t(`state.event.${cardTransitions[i].event}`);
  return `<svg viewBox="0 0 560 250" role="img" aria-label="${t("state.diagram")}" class="state__svg">
    <defs>
      <marker id="arrow-on" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10z" fill="var(--rune-ok)"/></marker>
      <marker id="arrow-off" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10z" fill="var(--ink-soft)"/></marker>
    </defs>
    ${arrow(0, "M140 98 C 230 40, 330 40, 410 88", 210, 38, label(0))}
    ${arrow(1, "M140 112 C 230 150, 330 150, 410 112", 222, 158, label(1))}
    ${arrow(2, "M80 125 L 80 186", 92, 165, label(2))}
    ${arrow(3, "M520 92 C 560 60, 560 140, 530 120", 430, 60, label(3))}
    ${box(20, 80, "ACTIVE")}${box(410, 80, "BLOCKED")}${box(20, 190, "EXPIRED")}
  </svg>`;
}

/** "ACTIVE —blocked by owner→ BLOCKED —expiry→ BLOCKED"; an invalid step ends with "✗". */
function walkText(t, events) {
  let state = "ACTIVE";
  const parts = [state];
  for (const e of events) {
    const next = cardTransitions.find((x) => x.from === state && x.event === e);
    parts.push(`—${t(`state.event.${e}`)}→`);
    if (!next) {
      parts.push(`✗ ${t("state.invalidStep")}`);
      break;
    }
    state = next.to;
    parts.push(state);
  }
  return parts.join(" ");
}

registerTrainer("state", ({ t }) => {
  const tests = [[]];
  const diagram = el("div", { className: "state__diagram" });
  const list = el("ol", { className: "state__tests" });
  const result = el("div", { className: "trainer__result", dataset: { testid: "trainer-result" }, attrs: { "aria-live": "polite" } });
  const update = () => {
    const filled = tests.filter((x) => x.length);
    const r = stateCoverage(cardTransitions, filled);
    diagram.innerHTML = stateDiagram(t, r.usedTransitions);
    list.replaceChildren(...tests.map((events) => el("li", { dataset: { testid: "state-test" } }, walkText(t, events))));
    if (!filled.length) return result.replaceChildren();
    const p = (x) => pct(x.covered, x.total);
    result.replaceChildren(
      ...verdict(t, p(r.valid), [
        el("p", { dataset: { testid: "state-states" } }, t("state.states", { pct: p(r.states), n: r.states.covered, total: r.states.total })),
        el("p", { dataset: { testid: "state-valid" } }, t("state.valid", { pct: p(r.valid), n: r.valid.covered, total: r.valid.total })),
        r.invalid.tried.length
          ? el(
              "p",
              { className: "trainer__note", dataset: { testid: "state-invalid" } },
              t("state.invalid", { list: r.invalid.tried.map((x) => `${x.from} + ${t(`state.event.${x.event}`)}`).join("; ") }),
              r.invalid.tried.some((x) => x.from === "EXPIRED" && x.event === "blockByClient") ? " " + t("state.bug13") : "",
            )
          : null,
      ]),
    );
  };
  const events = el(
    "div",
    { className: "state__events" },
    ...cardEvents.map((e) =>
      el("button", {
        type: "button",
        className: "button button--quiet",
        textContent: `+ ${t(`state.event.${e}`)}`,
        dataset: { testid: `event-${e}` },
        onclick: () => (tests.at(-1).push(e), update()),
      }),
    ),
  );
  const controls = el(
    "div",
    { className: "state__controls" },
    el("button", { type: "button", className: "button", textContent: t("state.newTest"), dataset: { testid: "state-new-test" }, onclick: () => tests.at(-1).length && (tests.push([]), update()) }),
    el("button", { type: "button", className: "button button--quiet", textContent: t("state.clear"), onclick: () => (tests.splice(0, tests.length, []), update()) }),
  );
  update();
  return el(
    "section",
    { className: "trainer", dataset: { testid: "trainer-state" } },
    el("h2", {}, t("state.title")),
    el("p", { className: "trainer__task" }, t("state.rules", { attempts: RULES.maxCvvAttempts })),
    diagram,
    events,
    el("p", { className: "trainer__label" }, t("state.testsLead")),
    list,
    controls,
    result,
  );
});

/** "6000 OTHER", "6000|OTHER", "5 000,00 GAMBLING" → program input, or null if unreadable. */
function programInput(programId, text) {
  if (programId === "commission") {
    const a = parseAmount(text);
    return a.ok ? (a.cents / 100).toFixed(2) : null;
  }
  const m = String(text).trim().match(/^(.*?)[\s|]+([A-Za-z_]+)$/);
  const a = m && parseAmount(m[1]);
  return a?.ok ? `${(a.cents / 100).toFixed(2)}|${m[2]}` : null;
}

registerTrainer("coverage", ({ t }) => {
  const controls = radios("cov-program", [["commission", t("cov.commission")], ["fraud", t("cov.fraud")]], "cov-program");
  const code = el("ol", { className: "code-listing" });
  const programId = () => controls.querySelector("input:checked").value;
  const showCode = (hit = []) =>
    code.replaceChildren(
      ...PROGRAMS[programId()].lines.map((line, i) =>
        el("li", { dataset: { testid: "code-line", hit: String(hit.includes(i + 1)) } }, el("code", {}, line)),
      ),
    );
  showCode();
  const input = el("textarea", { className: "trainer__input", rows: 3, dataset: { testid: "trainer-input" }, attrs: { "aria-label": t("trainer.inputLabel") } });
  const setPlaceholder = () => (input.placeholder = t(`cov.placeholder.${programId()}`));
  setPlaceholder();
  controls.addEventListener("change", () => (showCode(), setPlaceholder()));
  const result = el("div", { className: "trainer__result", dataset: { testid: "trainer-result" }, attrs: { "aria-live": "polite" } });
  const button = el("button", { type: "button", className: "button", textContent: t("trainer.check"), dataset: { testid: "trainer-check" } });
  button.addEventListener("click", () => {
    const id = programId();
    const values = splitValues(input.value);
    const inputs = values.map((v) => programInput(id, v));
    const invalid = values.filter((_, i) => inputs[i] === null);
    const ok = inputs.filter(Boolean);
    if (!ok.length) return result.replaceChildren(invalidLine(t, invalid.length ? invalid : ["—"]));
    const r = codeTrace(id, ok);
    showCode(r.lines);
    const missingEdges = PROGRAMS[id].edges.filter((e) => !r.edges.includes(e));
    result.replaceChildren(
      ...verdict(t, r.branch, [
        el("p", { dataset: { testid: "cov-statement" } }, t("cov.statement", { pct: r.statement })),
        el("p", { dataset: { testid: "cov-branch" } }, t("cov.branch", { pct: r.branch, edges: r.edges.join(", ") || "—" })),
        missingEdges.length ? el("p", { dataset: { testid: "missing" } }, t("cov.missing", { edges: missingEdges.join(", ") })) : null,
        invalidLine(t, invalid),
      ]),
    );
  });
  return el(
    "section",
    { className: "trainer", dataset: { testid: "trainer-coverage" } },
    el("h2", {}, t("cov.title")),
    el("p", { className: "trainer__task" }, t("cov.rules")),
    controls,
    code,
    el("label", { className: "trainer__label" }, t("trainer.inputLabel"), el("small", {}, t("cov.hint"))),
    input,
    el("div", { className: "trainer__actions" }, button),
    result,
  );
});

registerTab("trainer", (ctx) => {
  const wrap = el("div", { className: "trainers" });
  wrap.append(el("p", { className: "trainers__lead" }, ctx.t("trainer.lead")));
  ctx.section.trainers.forEach((kind) => builders[kind] && wrap.append(builders[kind](ctx)));
  return wrap;
});
