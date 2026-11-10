// Card Wallet rules used by the technique trainers. Pure data and functions, no DOM.
// Every number here is pinned to the wallet code by tests/unit/test_istqb_wallet_rules.py (NFR-12).

export const RULES = {
  fraudThreshold: "5000.00", // fraud-service/fraud_service/rules.py HIGH_AMOUNT_THRESHOLD
  amountMin: "0.01", // wallet-api/app/schemas/common.py Amount: gt=0
  amountMax: "10000.00", // Amount: le=10000.00
  dailyLimitMin: "1.00", // wallet-api/app/schemas/cards.py DailyLimit
  dailyLimitMax: "10000.00",
  dailyLimitDefault: "1000.00",
  minCommission: "0.50", // wallet-api/app/services/money.py MIN_COMMISSION
  maxCvvAttempts: 3, // wallet-api/app/services/payments.py MAX_FAILED_CVV_ATTEMPTS
  currencies: ["EUR", "USD", "PLN"],
  categories: ["GROCERIES", "ELECTRONICS", "TRAVEL", "RESTAURANTS", "GAMBLING", "OTHER"],
  cardStates: ["ACTIVE", "BLOCKED", "EXPIRED"],
};

export const toCents = (text) => Math.round(Number(text) * 100);
export const THRESHOLD = toCents(RULES.fraudThreshold);

/** The Fraud Service decision for an amount in cents (BR-FRD-01): first matching rule wins. */
export function fraudDecision(cents, category) {
  if (cents > THRESHOLD) return { decision: "DECLINE", reason: "HIGH_AMOUNT" };
  if (category === "GAMBLING") return { decision: "DECLINE", reason: "BLOCKED_CATEGORY" };
  return { decision: "APPROVE", reason: "" };
}

/**
 * Card status model from the requirements (BR-CARD-04…06). Events: wrongCvv3 = third wrong CVV
 * in a row; blockByClient; expiryPassed = the date passes the expiry date. A blocked card stays
 * BLOCKED after its expiry date. Only an ACTIVE card may be blocked by its owner — the code also
 * lets an EXPIRED card be blocked, which is the open defect BUG-13 (an invalid transition that
 * the system wrongly accepts).
 */
export const cardTransitions = [
  { from: "ACTIVE", event: "wrongCvv3", to: "BLOCKED" },
  { from: "ACTIVE", event: "blockByClient", to: "BLOCKED" },
  { from: "ACTIVE", event: "expiryPassed", to: "EXPIRED" },
  { from: "BLOCKED", event: "expiryPassed", to: "BLOCKED" },
];

export const cardEvents = ["wrongCvv3", "blockByClient", "expiryPassed"];

/**
 * Small programs for statement and branch coverage, written as pseudo-code of real wallet
 * functions. Lines are numbered from 1. edges = the branches of the control flow graph
 * (§4.3.2: unconditional and conditional). run(input) returns the executed lines and edges.
 */
export const PROGRAMS = {
  commission: {
    // wallet-api/app/services/money.py calculate_commission, with max() written as an if
    lines: [
      "commission = round_half_up(amount * 0.01)",
      "if commission < 0.50:",
      "    commission = 0.50",
      "return commission",
    ],
    edges: ["1→2", "2→3", "2→4", "3→4"],
    inputHint: "10.00",
    run(input) {
      const small = Math.round(toCents(input) / 100) < toCents(RULES.minCommission);
      return small
        ? { lines: [1, 2, 3, 4], edges: ["1→2", "2→3", "3→4"] }
        : { lines: [1, 2, 4], edges: ["1→2", "2→4"] };
    },
  },
  fraud: {
    // fraud-service/fraud_service/rules.py evaluate; each return ends the function
    lines: [
      "if amount > 5000.00:",
      "    return DECLINE, HIGH_AMOUNT",
      'if category == "GAMBLING":',
      "    return DECLINE, BLOCKED_CATEGORY",
      "return APPROVE",
    ],
    edges: ["1→2", "1→3", "3→4", "3→5"],
    inputHint: "6000|OTHER",
    run(input) {
      const [amount, category] = input.split("|");
      if (toCents(amount) > THRESHOLD) return { lines: [1, 2], edges: ["1→2"] };
      if ((category ?? "").trim() === "GAMBLING") return { lines: [1, 3, 4], edges: ["1→3", "3→4"] };
      return { lines: [1, 3, 5], edges: ["1→3", "3→5"] };
    },
  },
};
