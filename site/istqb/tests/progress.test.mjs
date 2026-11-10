// Storage that can be read but not written (quota full, some private modes) must not lose state.
import { test } from "node:test";
import assert from "node:assert/strict";

globalThis.window = {
  localStorage: {
    getItem: () => JSON.stringify({ prefs: { lang: "ru" } }),
    setItem: () => {
      throw new Error("QuotaExceededError");
    },
  },
};
const progress = await import("../js/progress.js");

test("exam state survives when writes fail but reads work", () => {
  progress.setExam({ ids: ["q-1"], answers: {} });
  assert.deepEqual(progress.getExam(), { ids: ["q-1"], answers: {} });
  progress.save("4.2", 5);
  assert.equal(progress.get().sections["4.2"].done, true);
  assert.equal(progress.getPref("lang", "en"), "ru", "what was readable is kept");
});
