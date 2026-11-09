// Sandbox: build a call (or pick a ready scenario), send the owl, read the time line and the rune.
// Answers come from sim.js, which CI checks against the real Fraud Service (NFR-10).

import { character } from "./art.js";
import { renderCompare } from "./compare.js";
import { run } from "./sim.js";
import { registerTab } from "./tabs.js";

const METHODS = ["CheckPayment", "GetDecision", "WatchRiskEvents", "CheckBatch", "ScorePayments"];
const STREAMING = new Set(["WatchRiskEvents", "CheckBatch", "ScorePayments"]);
const CATEGORIES = ["GROCERIES", "ELECTRONICS", "TRAVEL", "RESTAURANTS", "GAMBLING", "OTHER"];
const MERCHANTS = ["Shop", "TEST_TIMEOUT", "TEST_ERROR"];
const SEALS = { wallet: "dev-wallet-key", monitor: "dev-monitor-key", forged: "forged-seal" };
const DEFAULT_METHOD = { server: "WatchRiskEvents", client: "CheckBatch", bidi: "ScorePayments" };
const REACTION = {
  OK: "happy", CANCELLED: "idle", DEADLINE_EXCEEDED: "panic", INTERNAL: "panic", UNAVAILABLE: "idle",
};
const ROW_KEYS = {
  call: "call", subscribed: "subscribed", event: "event", filtered: "filtered", answer: "answer",
  payment: "payment", "end of sending": "endOfSending", summary: "summary", "more payments": "morePayments",
};

const scenariosReady = fetch(new URL("../scenarios.json", import.meta.url)).then((r) => r.json());
const reduceMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "testid") node.dataset.testid = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v);
  }
  node.append(...children);
  return node;
}

function field(label, control) {
  return el("label", { class: "field" }, el("span", { class: "field__label", text: label }), control);
}

function select(options, value) {
  const s = el("select");
  for (const [v, text] of options) {
    const o = el("option", { value: v, text });
    if (v === value) o.selected = true;
    s.append(o);
  }
  return s;
}

/** Scenario (scenarios.json shape) → the same call in Python and in Postman. */
export function codeFor(s) {
  const seal = s.seal === undefined ? "wallet" : s.seal;
  const md = [];
  if (seal) md.push(`("x-api-key", "${SEALS[seal]}")`);
  if (s.requestId) md.push(`("x-request-id", "${s.requestId}")`);
  const deadline = s.deadline ?? 2;
  const pay = (p = {}) => {
    const args = [];
    if (p.amount) args.push(`amount="${p.amount}"`);
    if (p.category) args.push(`merchant_category="${p.category}"`);
    if (p.merchant) args.push(`merchant_name="${p.merchant}"`);
    return `payment(${args.join(", ")})`;
  };
  const payments = s.batchSize ? [] : (s.payments ?? [{}]);
  const list = s.batchSize
    ? `(payment() for _ in range(${s.batchSize}))`
    : `iter([${payments.map(pay).join(", ")}])`;
  const call = {
    CheckPayment: `answer = stub.CheckPayment(${pay(payments[0])}, metadata=metadata, timeout=${deadline})`,
    GetDecision: `answer = stub.GetDecision(\n    fraud_pb2.GetDecisionRequest(transaction_id="no-such-id"),\n    metadata=metadata, timeout=${deadline})`,
    WatchRiskEvents: `for event in stub.WatchRiskEvents(\n        fraud_pb2.WatchRiskEventsRequest(min_risk_score=${s.minRiskScore ?? 0}),\n        metadata=metadata, timeout=${deadline}):\n    print(event.risk_score, event.reason)`,
    CheckBatch: `summary = stub.CheckBatch(${list}, metadata=metadata, timeout=${deadline})`,
    ScorePayments: `for answer in stub.ScorePayments(${list}, metadata=metadata, timeout=${deadline}):\n    print(answer.transaction_id, answer.decision)`,
  }[s.method];
  const python = [
    "import grpc",
    "from fraudpb import fraud_pb2, fraud_pb2_grpc",
    "from lab import payment  # grpc-lab/lab.py",
    "",
    'stub = fraud_pb2_grpc.FraudServiceStub(grpc.insecure_channel("localhost:50051"))',
    `metadata = (${md.join(", ")}${md.length === 1 ? "," : ""})`,
    call,
  ].join("\n");
  const message = {
    CheckPayment: JSON.stringify({ amount: payments[0]?.amount ?? "10.00", merchant_category: payments[0]?.category ?? "GROCERIES", merchant_name: payments[0]?.merchant ?? "Shop" }),
    GetDecision: '{"transaction_id": "no-such-id"}',
    WatchRiskEvents: JSON.stringify({ min_risk_score: s.minRiskScore ?? 0 }),
    CheckBatch: "one message per payment, then End streaming",
    ScorePayments: "one message per payment, then End streaming",
  }[s.method];
  const postman = [
    "New → gRPC → localhost:50051",
    `Method: fraud.v1.FraudService/${s.method}`,
    `Metadata: ${seal ? `x-api-key: ${SEALS[seal]}` : "(none)"}${s.requestId ? `, x-request-id: ${s.requestId}` : ""}`,
    `Message: ${message}`,
  ].join("\n");
  return { python, postman };
}

function rowText(row, t) {
  const b = row.body ?? {};
  if (row.dir === "end") return row.code;
  const head = t(`sb.row.${ROW_KEYS[row.label] ?? "call"}`, { method: b.method ?? "", count: b.count ?? "" });
  if (b.decision) return `${head}: ${b.decision}, risk ${b.riskScore}${b.reason ? `, ${b.reason}` : ""}`;
  if (row.label === "filtered") return `${head}: risk ${b.riskScore}`;
  if (row.label === "payment") return `${head} ${b.index + 1}: ${b.amount} ${b.category} ${b.merchant}`;
  if (row.label === "summary") return `${head}: ${b.total} / ${b.approved} / ${b.declined}`;
  return head;
}

registerTab("sandbox", (lesson, { t }) => {
  if (lesson.sandboxMode === "compare") return renderCompare(t);
  const root = el("div", { class: "sandbox" });
  let state = {
    method: DEFAULT_METHOD[lesson.callType] ?? "CheckPayment",
    seal: "wallet",
    requestId: "",
    deadline: 2,
    minRiskScore: 0,
    payments: [{ amount: "10.00", category: "GROCERIES", merchant: "Shop" }],
  };

  const presetBox = el("section", { class: "sandbox__presets" }, el("h2", { text: t("sb.presets") }));
  const form = el("form", { class: "sandbox__form" });
  const result = el("section", { class: "sandbox__result", "aria-live": "polite" });
  root.append(presetBox, form, result);

  function drawForm() {
    form.replaceChildren();
    const method = select(METHODS.map((m) => [m, m]), state.method);
    method.addEventListener("change", () => {
      state = { ...state, method: method.value, openWatchers: 0, openStreams: 0 };
      drawForm();
    });
    const seal = select(
      ["wallet", "monitor", "forged", "none"].map((s) => [s, t(`sb.seal.${s}`)]),
      state.seal ?? "none",
    );
    seal.addEventListener("change", () => { state.seal = seal.value === "none" ? null : seal.value; });
    const rid = el("input", { type: "text", value: state.requestId ?? "", placeholder: "lab-1" });
    rid.addEventListener("input", () => { state.requestId = rid.value; });
    const out = el("output", { text: `${state.deadline}` });
    const deadline = el("input", { type: "range", min: "0.5", max: "8", step: "0.5", value: String(state.deadline) });
    deadline.addEventListener("input", () => { state.deadline = Number(deadline.value); out.textContent = deadline.value; });
    const top = el("div", { class: "sandbox__row" },
      field(t("sb.method"), method), field(t("sb.seal"), seal), field(t("sb.requestId"), rid),
      field(t("sb.deadline"), el("span", { class: "range" }, deadline, out)));
    form.append(top);

    if (state.method === "WatchRiskEvents") {
      const min = el("input", { type: "number", value: String(state.minRiskScore ?? 0), step: "10" });
      min.addEventListener("input", () => { state.minRiskScore = Number(min.value); });
      form.append(field(t("sb.minRisk"), min));
    }

    if (state.method !== "GetDecision") {
      const list = el("div", { class: "sandbox__payments" },
        el("p", { class: "field__label", text: t(state.method === "WatchRiskEvents" ? "sb.watchPayments" : "sb.payments") }));
      (state.payments ?? []).forEach((p, i) => {
        const amount = el("input", { type: "text", value: p.amount ?? "10.00", "aria-label": t("sb.amount") });
        amount.addEventListener("input", () => { state.payments[i].amount = amount.value; });
        const cat = select(CATEGORIES.map((c) => [c, c]), p.category ?? "GROCERIES");
        cat.setAttribute("aria-label", t("sb.category"));
        cat.addEventListener("change", () => { state.payments[i].category = cat.value; });
        const mer = select(MERCHANTS.map((m) => [m, m]), p.merchant ?? "Shop");
        mer.setAttribute("aria-label", t("sb.merchant"));
        mer.addEventListener("change", () => { state.payments[i].merchant = mer.value; });
        const remove = el("button", { type: "button", class: "link", text: t("sb.remove") });
        remove.addEventListener("click", () => { state.payments.splice(i, 1); drawForm(); });
        list.append(el("div", { class: "payment" }, el("span", { class: "payment__n", text: `${i + 1}` }), amount, cat, mer, remove));
      });
      const add = el("button", { type: "button", class: "button button--quiet", text: t("sb.addOwl") });
      add.addEventListener("click", () => {
        state.payments = [...(state.payments ?? []), { amount: "10.00", category: "GROCERIES", merchant: "Shop" }];
        drawForm();
      });
      list.append(add);
      form.append(list);
    }

    if (state.openWatchers || state.openStreams) {
      form.append(el("p", { class: "sandbox__setup", text: t("sb.setup", { watchers: state.openWatchers ?? 0, streams: state.openStreams ?? 0 }) }));
    }

    const send = el("button", { type: "submit", class: "button", testid: "sandbox-send", text: t("sb.send") });
    const actions = el("div", { class: "sandbox__actions" }, send);
    if (STREAMING.has(state.method)) {
      const cancel = el("button", { type: "button", class: "button button--quiet", text: t("sb.sendCancel") });
      cancel.addEventListener("click", () => fire({ ...current(), clientAction: "cancel" }));
      actions.append(cancel);
    }
    form.append(actions);
  }

  function current() {
    const s = {
      method: state.method,
      seal: state.seal === undefined ? "wallet" : state.seal,
      deadline: state.deadline,
      payments: (state.payments ?? []).map((p) => ({ ...p })),
      minRiskScore: state.minRiskScore,
      openWatchers: state.openWatchers,
      openStreams: state.openStreams,
      batchSize: state.batchSize,
      unknownTransaction: state.method === "GetDecision" ? true : undefined,
    };
    if (state.requestId) s.requestId = state.requestId;
    return s;
  }

  function fire(scenario) {
    const r = run(scenario);
    const timeline = el("ol", { class: "timeline", testid: "sandbox-timeline" });
    const rows = r.timeline.map((row) =>
      el("li", { class: `timeline__row timeline__row--${row.dir}`, testid: "sandbox-row" },
        el("span", { class: "timeline__t", text: `${row.t.toFixed(1)} s` }),
        el("span", { class: "timeline__dir", text: t(`sb.dir.${row.dir}`) }),
        el("span", { class: "timeline__text", text: rowText(row, t) })));
    timeline.append(...rows);

    const streamEnd = scenario.method === "WatchRiskEvents" && ["DEADLINE_EXCEEDED", "CANCELLED"].includes(r.code);
    const tone = r.code === "OK" ? "ok" : streamEnd ? "neutral" : "bad";
    const rune = el("div", { class: `rune rune--${tone}` },
      el("p", { class: "rune__code" }, el("span", { testid: "sandbox-rune-code", text: r.code }), el("span", { class: "rune__num", text: ` (${r.number})` })),
      el("p", { class: "rune__meaning", text: t(`code.${r.code}.meaning`) }),
      el("p", { class: "rune__retry", text: `${t("sb.retry")}: ${t(`code.${r.code}.retry`)}` }),
      el("p", { class: "rune__trailers", text: `${t("sb.trailers")}: ${Object.entries(r.trailers).map(([k, v]) => `${k}: ${v}`).join(", ") || "—"}` }));
    if (r.details) rune.append(el("p", { class: "rune__details", text: `details: ${r.details}` }));

    const reaction = el("div", { class: "reaction" });
    reaction.innerHTML = character("inspector", streamEnd ? "idle" : REACTION[r.code] ?? "stern", t("char.inspector"));
    reaction.append(el("p", { class: "reaction__bubble", text: t(streamEnd && r.code === "DEADLINE_EXCEEDED" ? "react.watchEnd" : `react.${r.code}`) }));

    const code = codeFor(scenario);
    const pre = el("pre", { class: "code", testid: "sandbox-code" });
    pre.textContent = `# Python\n${code.python}\n\n# Postman\n${code.postman}`;
    pre.hidden = true;
    const toggle = el("button", { type: "button", class: "button button--quiet", testid: "sandbox-code-toggle", "aria-expanded": "false", text: t("sb.codeShow") });
    toggle.addEventListener("click", () => {
      pre.hidden = !pre.hidden;
      toggle.setAttribute("aria-expanded", String(!pre.hidden));
      toggle.textContent = t(pre.hidden ? "sb.codeShow" : "sb.codeHide");
    });

    result.replaceChildren(
      el("h2", { text: t("sb.timeline") }), timeline,
      el("div", { class: "sandbox__verdict" }, rune, reaction),
      toggle, pre);

    if (!reduceMotion()) {
      rows.forEach((row, i) => row.animate([{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }],
        { duration: 220, delay: i * 260, fill: "backwards" }));
      rune.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 250, delay: rows.length * 260, fill: "backwards" });
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    fire(current());
  });

  scenariosReady.then((all) => {
    const byId = Object.fromEntries(all.map((s) => [s.id, s]));
    for (const id of lesson.presets ?? []) {
      const b = el("button", { type: "button", class: "preset", testid: `preset-${id}`, text: t(`preset.${id}`) });
      b.addEventListener("click", () => {
        const { expect: _expect, id: _id, lesson: _lesson, ...scenario } = byId[id];
        state = {
          ...state,
          ...scenario,
          seal: scenario.seal === undefined ? "wallet" : scenario.seal,
          deadline: scenario.deadline ?? 2,
          payments: scenario.batchSize ? [] : (scenario.payments ?? [{}]).map((p) => ({ amount: "10.00", category: "GROCERIES", merchant: "Shop", ...p })),
        };
        drawForm();
        fire(scenario);
      });
      presetBox.append(b);
    }
  });

  drawForm();
  result.append(el("p", { class: "placeholder-note", text: t("sb.empty") }));
  return root;
});
