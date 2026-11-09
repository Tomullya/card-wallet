// Simulator must give the same answers as the real Fraud Service (NFR-10).
// The same scenarios run against the service in tests/grpc/test_sandbox_scenarios.py.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { run } from "../js/sim.js";

const scenarios = JSON.parse(
  readFileSync(new URL("../scenarios.json", import.meta.url), "utf8"),
);

function checkExpect(result, expect) {
  assert.equal(result.code, expect.code, "status code");
  const field = (name) => result.answers.map((a) => a[name]);
  if (expect.decisions) assert.deepEqual(field("decision"), expect.decisions, "decisions");
  if (expect.reasons) assert.deepEqual(field("reason"), expect.reasons, "reasons");
  if (expect.riskScores) assert.deepEqual(field("riskScore"), expect.riskScores, "risk scores");
  if (expect.summary) assert.deepEqual(result.summary, expect.summary, "summary");
  if (expect.trailerRequestId) {
    const got = result.trailers["x-request-id"];
    if (expect.trailerRequestId === "absent") assert.equal(got, undefined, "no trailer");
    else if (expect.trailerRequestId === "generated") assert.ok(got, "generated trailer");
    else assert.equal(got, expect.trailerRequestId, "echoed trailer");
  }
}

for (const scenario of scenarios) {
  test(`scenario ${scenario.id}`, () => checkExpect(run(scenario), scenario.expect));
}

test("bidi cancel before first message", () => {
  const r = run({ method: "ScorePayments", payments: [], clientAction: "cancel" });
  assert.equal(r.code, "CANCELLED");
  assert.equal(r.answers.length, 0);
});

test("timeline is time-ordered and ends with the status", () => {
  for (const scenario of scenarios) {
    const { timeline, code } = run(scenario);
    for (let i = 1; i < timeline.length; i++) {
      assert.ok(timeline[i].t >= timeline[i - 1].t, `${scenario.id}: row ${i} goes back in time`);
    }
    assert.equal(timeline.at(-1).dir, "end", `${scenario.id}: last row is the status`);
    assert.equal(timeline.at(-1).code, code);
  }
});

test("status numbers match gRPC", () => {
  const r = run({ method: "CheckPayment", seal: null });
  assert.equal(r.number, 16);
});
