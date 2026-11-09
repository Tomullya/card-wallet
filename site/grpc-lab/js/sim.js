// Simulator of the Fraud Service for the sandbox (NFR-10).
// Mirrors fraud-service/fraud_service/server.py and auth.py; checked against the real service
// by tests/grpc/test_sandbox_scenarios.py using the same scenarios.json.

export const LIMITS = {
  threshold: 5000,
  maxBatch: 1000,
  maxWatchers: 8,
  maxStreams: 16,
  testTimeout: 5,
};

export const CODES = {
  OK: 0, CANCELLED: 1, INVALID_ARGUMENT: 3, DEADLINE_EXCEEDED: 4, NOT_FOUND: 5,
  PERMISSION_DENIED: 7, RESOURCE_EXHAUSTED: 8, UNIMPLEMENTED: 12, INTERNAL: 13,
  UNAVAILABLE: 14, UNAUTHENTICATED: 16,
};

const MONITOR_METHODS = new Set(["WatchRiskEvents", "GetDecision"]);
const DEFAULT_PAYMENT = { amount: "10.00", category: "GROCERIES", merchant: "Shop" };
const DECIMAL = /^([+-]?)(\d*)(?:\.(\d*))?(?:[eE]([+-]?\d+))?$/;
const STEP = 0.1; // simulated seconds between rows

/** Fill in scenario defaults (same defaults as scenarios.json documents). */
export function normalize(s) {
  const base = s.batchSize
    ? Array.from({ length: s.batchSize }, () => ({}))
    : (s.payments ?? [{}]);
  return {
    method: s.method,
    seal: s.seal === undefined ? "wallet" : s.seal,
    requestId: s.requestId ?? null,
    deadline: s.deadline ?? 2,
    payments: base.map((p, i) => ({ ...DEFAULT_PAYMENT, id: `tx-${i + 1}`, ...p })),
    minRiskScore: s.minRiskScore ?? 0,
    openWatchers: s.openWatchers ?? 0,
    openStreams: s.openStreams ?? 0,
    unknownTransaction: Boolean(s.unknownTransaction),
    clientAction: s.clientAction ?? "finish",
    buggy: Boolean(s.buggy),
  };
}

/**
 * Exact decimal like Python's Decimal: {mant: BigInt, exp: BigInt} or null.
 * Accepts surrounding spaces, full-width digits (NFKC) and "_" between digits, as Python does.
 */
export function decimalOf(text) {
  let s = String(text ?? "").normalize("NFKC").trim();
  if (s.includes("_")) {
    s = s.replace(/(?<=\d)_(?=\d)/g, "");
    if (s.includes("_")) return null;
  }
  const m = s.match(DECIMAL);
  if (!m || (!m[2] && !m[3])) return null;
  const frac = m[3] ?? "";
  let mant = BigInt((m[2] ?? "") + frac || "0");
  if (m[1] === "-") mant = -mant;
  return { mant, exp: BigInt(m[4] ?? "0") - BigInt(frac.length) };
}

/** d > n for an integer n, without floating-point rounding. */
function greaterThan(d, n) {
  if (d.exp > 1000n) return d.mant > 0n; // astronomically large (or negative) amounts
  if (d.exp < -1000n) return n < 0;      // |value| < 1: above n only when n is negative
  return d.exp >= 0n ? d.mant * 10n ** d.exp > BigInt(n) : d.mant > BigInt(n) * 10n ** -d.exp;
}

/** Decision rules, BR-FRD-01. */
export function evaluate(payment) {
  const amount = decimalOf(payment.amount);
  if (amount && greaterThan(amount, LIMITS.threshold)) return { decision: "DECLINE", reason: "HIGH_AMOUNT", riskScore: 90 };
  if (payment.category === "GAMBLING") {
    return { decision: "DECLINE", reason: "BLOCKED_CATEGORY", riskScore: 80 };
  }
  return { decision: "APPROVE", reason: "", riskScore: 10 };
}

function validAmount(text) {
  return decimalOf(text) !== null;
}

/** Run one call and return the status, answers and a time line of messages. */
export function run(scenario) {
  const s = normalize(scenario);
  const timeline = [];
  const answers = [];
  let t = 0;     // drawing time for the time line
  let busy = 0;  // server time that counts against the deadline (only TEST_TIMEOUT sleeps)
  let summary;
  const generatedId = "a8f3c1d2-7b4e-4c55-9e0a-5d1f2b3c4e6f";
  const requestId = s.requestId ?? generatedId;
  let authFailure = false;

  const row = (dir, label, body = {}) => timeline.push({ t: round(t), dir, label, body });

  const finish = (code, details = "") => {
    // BUG-19 (buggy mode): the trailer survives only on authentication errors.
    // When the client ends the call (deadline, cancel) no trailers reach it.
    const clientEnded = code === "DEADLINE_EXCEEDED" || code === "CANCELLED";
    const trailers = clientEnded || (s.buggy && !authFailure) ? {} : { "x-request-id": requestId };
    timeline.push({ t: round(t), dir: "end", label: code, code, details, trailers });
    return { code, number: CODES[code], details, timeline, trailers, answers, summary };
  };

  row("out", "call", { method: s.method, seal: s.seal, requestId: s.requestId });

  // Interceptor: API key and role (BR-FRD-04).
  if (s.seal === null || s.seal === "forged") {
    authFailure = true;
    if (s.seal === "forged" && s.buggy) return finish("PERMISSION_DENIED", "unknown x-api-key");
    return finish("UNAUTHENTICATED", "missing or unknown x-api-key");
  }
  if (s.seal === "monitor" && !MONITOR_METHODS.has(s.method)) {
    authFailure = true;
    return finish("PERMISSION_DENIED", `role monitor may not call ${s.method}`);
  }

  // Scores one payment like server.score(); returns a status code on failure or null.
  const score = (p, index) => {
    const where = index === undefined ? "" : ` (index ${index})`;
    if (p.merchant === "TEST_ERROR") return ["INTERNAL", `Simulated fraud service error${where}`];
    if (p.merchant === "TEST_TIMEOUT") {
      busy += LIMITS.testTimeout;
      t += LIMITS.testTimeout;
      // At exactly 5 s the real service races; most runs end with DEADLINE_EXCEEDED.
      if (busy >= s.deadline) return ["DEADLINE_EXCEEDED", "Deadline Exceeded"];
    }
    if (!validAmount(p.amount)) return ["INVALID_ARGUMENT", `amount must be a decimal number${where}`];
    return null;
  };

  const answer = (p) => {
    const a = { transactionId: p.id, ...evaluate(p) };
    answers.push(a);
    return a;
  };

  switch (s.method) {
    case "CheckPayment": {
      const p = s.payments[0] ?? { ...DEFAULT_PAYMENT, id: "tx-1" };
      const failed = score(p);
      if (failed) {
        if (failed[0] === "DEADLINE_EXCEEDED") t = s.deadline;
        return finish(...failed);
      }
      t += STEP;
      row("in", "answer", answer(p));
      return finish("OK");
    }

    case "GetDecision":
      t += STEP;
      if (s.unknownTransaction) return finish("NOT_FOUND", "unknown transaction_id");
      row("in", "answer", answer(s.payments[0]));
      return finish("OK");

    case "WatchRiskEvents": {
      if (s.minRiskScore < 0 || s.minRiskScore > 100) {
        return finish("INVALID_ARGUMENT", "min_risk_score must be 0-100");
      }
      if (s.openWatchers >= LIMITS.maxWatchers) {
        return finish("RESOURCE_EXHAUSTED", `too many watchers (max ${LIMITS.maxWatchers})`);
      }
      row("in", "subscribed", { "x-subscribed": "true" });
      for (const p of s.payments) {
        t += 3 * STEP;
        if (t >= s.deadline) break;
        // Another client's call that fails (or that its client abandons at 2 s) publishes nothing.
        if (p.merchant === "TEST_ERROR" || p.merchant === "TEST_TIMEOUT" || !validAmount(p.amount)) {
          row("skip", "not published", { transactionId: p.id, merchant: p.merchant, amount: p.amount });
          continue;
        }
        const decided = evaluate(p);
        if (decided.riskScore >= s.minRiskScore) {
          row("in", "event", answer(p));
        } else {
          row("skip", "filtered", { transactionId: p.id, riskScore: decided.riskScore });
        }
      }
      if (s.clientAction === "cancel") {
        t += STEP;
        return finish("CANCELLED", "Cancelled by the client");
      }
      t = Math.max(t, s.deadline);
      return finish("DEADLINE_EXCEEDED", "Deadline Exceeded");
    }

    case "CheckBatch": {
      if (s.openStreams >= LIMITS.maxStreams) {
        return finish("RESOURCE_EXHAUSTED", `too many open streams (max ${LIMITS.maxStreams})`);
      }
      const sent = s.payments.slice(0, LIMITS.maxBatch + 1);
      sendRows(sent);
      if (sent.length > LIMITS.maxBatch) {
        return finish("RESOURCE_EXHAUSTED", `batch too large (max ${LIMITS.maxBatch})`);
      }
      if (s.clientAction === "cancel") return finish("CANCELLED", "Cancelled by the client");
      t += STEP;
      row("out", "end of sending");
      if (sent.length === 0) return finish("INVALID_ARGUMENT", "batch is empty");
      const bad = sent.findIndex((p) => !validAmount(p.amount));
      if (bad >= 0) return finish("INVALID_ARGUMENT", `amount must be a decimal number (index ${bad})`);
      const scored = [];
      for (const [i, p] of sent.entries()) {
        const failed = score(p, i);
        if (failed) return finish(...failed);
        scored.push(evaluate(p));
      }
      const declined = sent.filter((p, i) => scored[i].decision === "DECLINE");
      summary = {
        total: sent.length,
        approved: sent.length - declined.length,
        declined: declined.length,
      };
      t += STEP;
      row("in", "summary", { ...summary, declinedTransactionIds: declined.map((p) => p.id) });
      return finish("OK");
    }

    case "ScorePayments": {
      if (s.openStreams >= LIMITS.maxStreams) {
        return finish("RESOURCE_EXHAUSTED", `too many open streams (max ${LIMITS.maxStreams})`);
      }
      for (const [i, p] of s.payments.entries()) {
        t += 3 * STEP;
        row("out", "payment", { index: i, ...p });
        const failed = score(p, i);
        if (failed) return finish(...failed);
        t += STEP;
        row("in", "answer", answer(p));
      }
      if (s.clientAction === "cancel") {
        t += STEP;
        return finish("CANCELLED", "Cancelled by the client");
      }
      t += STEP;
      row("out", "end of sending");
      if (s.buggy) {
        // BUG-18: the server never ends its side; the client's deadline does.
        t = Math.max(t, s.deadline);
        return finish("DEADLINE_EXCEEDED", "Deadline Exceeded");
      }
      return finish("OK");
    }

    default:
      return finish("UNIMPLEMENTED", `unknown method ${s.method}`);
  }

  function sendRows(payments) {
    const shown = payments.length > 12 ? payments.slice(0, 3) : payments;
    for (const [i, p] of shown.entries()) {
      t += STEP;
      row("out", "payment", { index: i, ...p });
    }
    if (shown.length < payments.length) {
      t += STEP;
      row("out", "more payments", { count: payments.length - shown.length });
    }
  }
}

function round(x) {
  return Math.round(x * 100) / 100;
}
