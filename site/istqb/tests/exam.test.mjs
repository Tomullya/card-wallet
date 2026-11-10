// Mock exam logic (NFR-11): 40 questions 8/6/4/11/9/2, 60 or 75 minutes, pass mark 26.
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  DISTRIBUTION,
  PASS_MARK,
  answer,
  buildExam,
  isRight,
  remaining,
  resume,
  score,
  startExam,
  submit,
} from "../js/exam.js";

/** A synthetic bank: `per` exam questions per chapter (+1 warm-up that must never be picked). */
function bank(per = 20) {
  const qs = [];
  for (const ch of ["1", "2", "3", "4", "5", "6"]) {
    for (let i = 0; i < per; i++) {
      qs.push({ id: `q-${ch}.1.1-${String(i).padStart(2, "0")}`, section: `${ch}.1`, answer: i % 7 === 0 ? [0, 2] : [1] });
    }
    qs.push({ id: `q-${ch}.1.1-w`, section: `${ch}.1`, answer: [0], exam: false });
  }
  return qs;
}

const MIN = 60 * 1000;

test("distribution is 8/6/4/11/9/2 = 40, pass mark 26", () => {
  assert.deepEqual(DISTRIBUTION, { 1: 8, 2: 6, 3: 4, 4: 11, 5: 9, 6: 2 });
  assert.equal(Object.values(DISTRIBUTION).reduce((a, b) => a + b), 40);
  assert.equal(PASS_MARK, 26);
});

test("buildExam picks the right number per chapter, no duplicates, no warm-ups", () => {
  const qs = bank();
  const ids = buildExam(qs, 42);
  assert.equal(ids.length, 40);
  assert.equal(new Set(ids).size, 40);
  assert.ok(ids.every((id) => !id.endsWith("-w")));
  const per = {};
  ids.forEach((id) => (per[id[2]] = (per[id[2]] ?? 0) + 1));
  assert.deepEqual(per, { 1: 8, 2: 6, 3: 4, 4: 11, 5: 9, 6: 2 });
});

test("buildExam is deterministic for a seed and differs between seeds", () => {
  const qs = bank();
  assert.deepEqual(buildExam(qs, 7), buildExam(qs, 7));
  assert.notDeepEqual(buildExam(qs, 7), buildExam(qs, 8));
});

test("buildExam explains a bank that is too small", () => {
  assert.throws(() => buildExam(bank(5), 1), /chapter 4: 5 of 11/);
});

test("score: pass at 26, fail at 25; select-TWO needs both answers", () => {
  const qs = bank();
  const ids = buildExam(qs, 3);
  const byId = Object.fromEntries(qs.map((q) => [q.id, q]));
  const answers = {};
  ids.forEach((id, i) => (answers[id] = i < 26 ? byId[id].answer : [4]));
  const pass = score(ids, answers, qs);
  assert.equal(pass.total, 26);
  assert.equal(pass.passed, true);
  answers[ids[0]] = [4];
  assert.equal(score(ids, answers, qs).passed, false);
  assert.equal(isRight({ answer: [0, 2] }, [0]), false);
  assert.equal(isRight({ answer: [0, 2] }, [2, 0]), true);
  assert.equal(isRight({ answer: [1] }, undefined), false);
});

test("score per chapter", () => {
  const qs = bank();
  const ids = buildExam(qs, 3);
  const r = score(ids, {}, qs);
  assert.deepEqual(r.byChapter["4"], { right: 0, of: 11 });
  assert.equal(r.total, 0);
});

test("timeout submits and unanswered are wrong", () => {
  const qs = bank();
  let s = startExam(qs, { seed: 1, now: 0, minutes: 60 });
  s = answer(s, s.ids[0], [1]);
  const later = resume(s, qs, 61 * MIN);
  assert.equal(later.submitted, true);
  assert.equal(later.result.byChapter["1"].of, 8);
  assert.ok(later.result.total <= 1);
  assert.equal(later.submittedAt, 60 * MIN, "submitted at the end of the time, not at reload time");
});

test("resume restores answers and remaining time", () => {
  const qs = bank();
  let s = startExam(qs, { seed: 5, now: 1000, minutes: 75 });
  s = answer(s, s.ids[3], [2]);
  const saved = JSON.parse(JSON.stringify(s)); // what localStorage gives back
  const back = resume(saved, qs, 1000 + 10 * MIN);
  assert.equal(back.submitted, false);
  assert.deepEqual(back.answers[s.ids[3]], [2]);
  assert.equal(remaining(back, 1000 + 10 * MIN), 65 * 60);
});

test("answers cannot change after submit", () => {
  const qs = bank();
  let s = submit(startExam(qs, { seed: 2, now: 0, minutes: 60 }), qs, 5 * MIN);
  const after = answer(s, s.ids[0], [1]);
  assert.equal(after.answers[s.ids[0]], undefined);
  assert.equal(remaining(s, 10 * MIN), 0);
});
