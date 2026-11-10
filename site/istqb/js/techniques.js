// Checkers for the test-technique trainers. Pure functions, no DOM.
// Money is handled in integer cents so that 5000.01 never becomes 5000.009999.

import { PROGRAMS, RULES, THRESHOLD, fraudDecision, toCents } from "./wallet-rules.js";

const MAX = toCents(RULES.amountMax);

/** "5 000,00" → 500000 cents. Spaces (also non-breaking) are ignored, comma = decimal point. */
export function parseAmount(text) {
  const clean = String(text)
    .replace(/[\s\u00a0\u202f]/g, "")
    .replace(/^[\u2212\u2013]/, "-") // the site prints "−0.01"; let it be pasted back
    .replace(",", ".");
  const m = clean.match(/^(-?)(\d+)(?:\.(\d{1,2}))?$/);
  if (!m) return { ok: false, error: "format" };
  const cents = Number(m[2]) * 100 + Number((m[3] ?? "").padEnd(2, "0"));
  return { ok: true, cents: m[1] ? -cents : cents };
}

/** Equivalence partitions of each trainer task, in display order. */
export const PARTITIONS = {
  amount: [
    { id: "le0", valid: false, test: (c) => c <= 0 },
    { id: "approve", valid: true, test: (c) => c > 0 && c <= THRESHOLD },
    { id: "high", valid: true, test: (c) => c > THRESHOLD && c <= MAX },
    { id: "over", valid: false, test: (c) => c > MAX },
  ],
  category: [
    { id: "allowed", valid: true, test: (v) => RULES.categories.includes(v) && fraudDecision(1, v).decision === "APPROVE" },
    { id: "gambling", valid: true, test: (v) => v === "GAMBLING" },
    { id: "unknown", valid: false, test: (v) => !RULES.categories.includes(v) },
  ],
};

function partitionOf(task, text) {
  if (task === "category") {
    const value = String(text).trim();
    return { value, part: PARTITIONS.category.find((p) => p.test(value)) };
  }
  const parsed = parseAmount(text);
  if (!parsed.ok) return { part: null };
  return { value: parsed.cents, part: PARTITIONS.amount.find((p) => p.test(parsed.cents)) };
}

/** Which partitions the test values cover, which are missing, and values that add nothing new. */
export function epCheck(task, values) {
  const seen = new Set();
  const duplicates = [];
  const invalid = [];
  for (const text of values) {
    if (String(text).trim() === "") continue;
    const { part } = partitionOf(task, text);
    if (!part) {
      invalid.push(String(text));
      continue;
    }
    if (seen.has(part.id)) duplicates.push([String(text).trim(), part.id]);
    seen.add(part.id);
  }
  const ids = PARTITIONS[task].map((p) => p.id);
  return {
    covered: ids.filter((id) => seen.has(id)),
    missing: ids.filter((id) => !seen.has(id)),
    duplicates,
    invalid,
  };
}

/** Boundary values: the smallest and largest value of each ordered partition (in cents). */
export const BOUNDARIES = {
  fraud: [THRESHOLD, THRESHOLD + 1], // ≤ 5000.00 approve | > 5000.00 decline
  amount: [0, 1, MAX, MAX + 1], // ≤ 0 invalid | 0.01…10000.00 valid | > 10000.00 invalid
};

/** 2-value BVA: each boundary value. 3-value BVA: each boundary value and both neighbours. */
export function bvaCheck(task, values, variant) {
  const base = BOUNDARIES[task];
  const required = [...new Set(variant === 3 ? base.flatMap((b) => [b - 1, b, b + 1]) : base)].sort(
    (a, b) => a - b,
  );
  const got = new Set();
  const invalid = [];
  for (const text of values) {
    if (String(text).trim() === "") continue;
    const parsed = parseAmount(text);
    if (parsed.ok) got.add(parsed.cents);
    else invalid.push(String(text));
  }
  return {
    required,
    covered: required.filter((v) => got.has(v)),
    missing: required.filter((v) => !got.has(v)),
    extra: [...got].filter((v) => !required.includes(v)).sort((a, b) => a - b),
    invalid,
  };
}

/** Action of the wallet for conditions [amount > 5000.00, category = GAMBLING]. */
function walletAction([high, gambling]) {
  const { reason } = fraudDecision(high ? THRESHOLD + 1 : 1, gambling ? "GAMBLING" : "OTHER");
  return { HIGH_AMOUNT: "DECLINE_HIGH", BLOCKED_CATEGORY: "DECLINE_CATEGORY" }[reason] ?? "APPROVE";
}

const ALL_COLUMNS = [
  [true, true],
  [true, false],
  [false, true],
  [false, false],
];
const same = (a, b) => a[0] === b[0] && a[1] === b[1];

/**
 * Check a decision table the learner built.
 * columns: [{c: [bool, bool], action: "APPROVE" | "DECLINE_HIGH" | "DECLINE_CATEGORY"}].
 */
export function decisionTable(columns) {
  const missing = ALL_COLUMNS.filter((c) => !columns.some((col) => same(col.c, c)));
  const contradictions = ALL_COLUMNS.filter((c) => {
    const actions = new Set(columns.filter((col) => same(col.c, c)).map((col) => col.action));
    return actions.size > 1;
  });
  const wrong = ALL_COLUMNS.filter((c) =>
    columns.some((col) => same(col.c, c) && col.action !== walletAction(c)),
  );
  return {
    columns: ALL_COLUMNS.map((c) => ({ c, action: walletAction(c) })),
    missing,
    contradictions,
    wrong,
    // amount > 5000.00 wins whatever the category, so those two columns merge into one ("-")
    minimised: [
      { c: [true, null], action: walletAction([true, false]) },
      { c: [false, true], action: walletAction([false, true]) },
      { c: [false, false], action: walletAction([false, false]) },
    ],
  };
}

/**
 * Run test cases (each a list of events, starting in the first state) through a state model.
 * An event with no transition from the current state is an invalid transition: it is recorded
 * and that test case stops there.
 */
export function stateCoverage(transitions, testCases, start = "ACTIVE") {
  const states = [...new Set(transitions.flatMap((x) => [x.from, x.to]))];
  const visited = new Set();
  const used = new Set();
  const tried = [];
  for (const events of testCases) {
    let state = start;
    visited.add(state);
    for (const event of events) {
      const i = transitions.findIndex((x) => x.from === state && x.event === event);
      if (i < 0) {
        if (!tried.some((x) => x.from === state && x.event === event)) tried.push({ from: state, event });
        break;
      }
      used.add(i);
      state = transitions[i].to;
      visited.add(state);
    }
  }
  return {
    states: { covered: visited.size, total: states.length },
    valid: { covered: used.size, total: transitions.length },
    usedTransitions: [...used].sort((a, b) => a - b),
    invalid: { tried },
  };
}

/** Statement and branch coverage of one of the PROGRAMS, plus the exercised lines and edges. */
export function codeTrace(programId, inputs) {
  const program = PROGRAMS[programId];
  const lines = new Set();
  const edges = new Set();
  for (const input of inputs) {
    const trace = program.run(input);
    trace.lines.forEach((l) => lines.add(l));
    trace.edges.forEach((e) => edges.add(e));
  }
  const pct = (n, total) => Math.round((100 * n) / total);
  return {
    statement: pct(lines.size, program.lines.length),
    branch: pct(edges.size, program.edges.length),
    lines: [...lines].sort((a, b) => a - b),
    edges: program.edges.filter((e) => edges.has(e)),
  };
}

/** Statement and branch coverage (whole percent) of one of the PROGRAMS for the inputs. */
export function codeCoverage(programId, inputs) {
  const { statement, branch } = codeTrace(programId, inputs);
  return { statement, branch };
}
