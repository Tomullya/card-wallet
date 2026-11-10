// Technique checkers used by the trainers (NFR-11) and the wallet rules they use (NFR-12).
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  bvaCheck,
  codeCoverage,
  decisionTable,
  epCheck,
  parseAmount,
  stateCoverage,
} from "../js/techniques.js";
import { PROGRAMS, RULES, cardTransitions, fraudDecision } from "../js/wallet-rules.js";

test("parseAmount accepts comma and spaces", () => {
  assert.deepEqual(parseAmount("5 000,00"), { ok: true, cents: 500000 });
  assert.deepEqual(parseAmount(" 5000.5 "), { ok: true, cents: 500050 });
  assert.deepEqual(parseAmount("5 000"), { ok: true, cents: 500000 });
  assert.deepEqual(parseAmount("-1"), { ok: true, cents: -100 });
  assert.deepEqual(parseAmount("0"), { ok: true, cents: 0 });
});

test("parseAmount rejects garbage", () => {
  for (const text of ["abc", "1.234", "", "1,2,3", "5e3", "--1", "1."]) {
    assert.deepEqual(parseAmount(text), { ok: false, error: "format" }, text);
  }
});

test("fraud rule matches the service", () => {
  assert.equal(RULES.fraudThreshold, "5000.00");
  assert.deepEqual(fraudDecision(500000, "GROCERIES"), { decision: "APPROVE", reason: "" });
  assert.deepEqual(fraudDecision(500001, "GAMBLING"), { decision: "DECLINE", reason: "HIGH_AMOUNT" });
  assert.deepEqual(fraudDecision(100, "GAMBLING"), { decision: "DECLINE", reason: "BLOCKED_CATEGORY" });
});

test("EP amount: covered, missing and duplicate partitions", () => {
  const r = epCheck("amount", ["100", "6000", "-5"]);
  assert.deepEqual(r.covered, ["le0", "approve", "high"]);
  assert.deepEqual(r.missing, ["over"]);
  assert.deepEqual(r.duplicates, []);
  const d = epCheck("amount", ["10", "20", "abc"]);
  assert.deepEqual(d.duplicates, [["20", "approve"]]);
  assert.deepEqual(d.invalid, ["abc"]);
});

test("EP category: partitions by behaviour, case matters", () => {
  const r = epCheck("category", ["TRAVEL", "GROCERIES", "groceries"]);
  assert.deepEqual(r.covered, ["allowed", "unknown"]);
  assert.deepEqual(r.missing, ["gambling"]);
  assert.deepEqual(r.duplicates, [["GROCERIES", "allowed"]]);
});

test("BVA 2-value around the fraud threshold", () => {
  const r = bvaCheck("fraud", ["5000", "5000,01"], 2);
  assert.deepEqual(r.required, [500000, 500001]);
  assert.deepEqual(r.missing, []);
});

test("BVA 3-value needs both neighbours of each boundary", () => {
  const r = bvaCheck("fraud", ["5000", "5000.01"], 3);
  assert.deepEqual(r.required, [499999, 500000, 500001, 500002]);
  assert.deepEqual(r.missing, [499999, 500002]);
});

test("BVA amount range has four boundary values", () => {
  const r = bvaCheck("amount", ["0.01", "10000"], 2);
  assert.deepEqual(r.required, [0, 1, 1000000, 1000001]);
  assert.deepEqual(r.missing, [0, 1000001]);
  assert.deepEqual(r.extra, []);
  assert.deepEqual(bvaCheck("amount", ["7"], 2).extra, [700]);
});

test("decision table: missing column, contradiction and wrong action", () => {
  const cols = [
    { c: [true, true], action: "DECLINE_HIGH" },
    { c: [true, false], action: "DECLINE_HIGH" },
    { c: [false, true], action: "DECLINE_CATEGORY" },
  ];
  const r = decisionTable(cols);
  assert.equal(r.columns.length, 4);
  assert.deepEqual(r.missing, [[false, false]]);
  assert.deepEqual(r.contradictions, []);
  assert.deepEqual(r.wrong, []);
  const bad = decisionTable([
    { c: [false, false], action: "APPROVE" },
    { c: [false, false], action: "DECLINE_HIGH" },
    { c: [true, true], action: "DECLINE_CATEGORY" },
  ]);
  assert.deepEqual(bad.contradictions, [[false, false]]);
  assert.deepEqual(bad.wrong, [[true, true], [false, false]]); // in table order
});

test("decision table minimises the high-amount columns", () => {
  const { minimised } = decisionTable([]);
  assert.deepEqual(minimised, [
    { c: [true, null], action: "DECLINE_HIGH" },
    { c: [false, true], action: "DECLINE_CATEGORY" },
    { c: [false, false], action: "APPROVE" },
  ]);
});

test("state coverage of card statuses", () => {
  assert.deepEqual(RULES.cardStates, ["ACTIVE", "BLOCKED", "EXPIRED"]);
  const one = stateCoverage(cardTransitions, [["wrongCvv3"]]);
  assert.deepEqual(one.states, { covered: 2, total: 3 });
  assert.deepEqual(one.valid, { covered: 1, total: cardTransitions.length });
  assert.deepEqual(one.invalid.tried, []);
  const r = stateCoverage(cardTransitions, [["blockByClient", "blockByClient"], ["expiryPassed"]]);
  assert.deepEqual(r.states, { covered: 3, total: 3 });
  assert.equal(r.valid.covered, 2);
  assert.deepEqual(r.invalid.tried, [{ from: "BLOCKED", event: "blockByClient" }]);
});

test("model follows the requirements: blocking an expired card is invalid (BUG-13)", () => {
  // BR-CARD-04 allows blocking only an ACTIVE card; the code allows it anyway — that is BUG-13.
  assert.ok(!cardTransitions.some((x) => x.from === "EXPIRED" && x.event === "blockByClient"));
  const r = stateCoverage(cardTransitions, [["expiryPassed", "blockByClient"]]);
  assert.deepEqual(r.invalid.tried, [{ from: "EXPIRED", event: "blockByClient" }]);
  assert.equal(cardTransitions.length, 4);
});

test("commission: branches include unconditional ones (control flow graph, §4.3.2)", () => {
  // edges: 1→2 (straight), 2→3 (if true), 2→4 (if false), 3→4 (straight) = 4 branches
  assert.equal(PROGRAMS.commission.edges.length, 4);
  assert.deepEqual(codeCoverage("commission", ["10.00"]), { statement: 100, branch: 75 });
  assert.deepEqual(codeCoverage("commission", ["100.00"]), { statement: 75, branch: 50 });
  assert.deepEqual(codeCoverage("commission", ["10.00", "100.00"]), { statement: 100, branch: 100 });
});

test("fraud function coverage", () => {
  assert.deepEqual(codeCoverage("fraud", ["6000|OTHER"]), { statement: 40, branch: 25 });
  assert.deepEqual(codeCoverage("fraud", ["6000|OTHER", "10|GAMBLING", "10|OTHER"]), { statement: 100, branch: 100 });
});

test("parseAmount accepts the minus sign the site itself prints (U+2212) and en dash", () => {
  assert.deepEqual(parseAmount("−0,01"), { ok: true, cents: -1 });
  assert.deepEqual(parseAmount("–5"), { ok: true, cents: -500 });
});
