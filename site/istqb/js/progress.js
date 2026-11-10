// Preferences, section progress and exam state, kept in the browser.
// Works without storage (memory only).

const KEY = "istqb-lab";
let memory = {};
let memoryOnly = false; // set once a write fails: storage can no longer be trusted

function readAll() {
  if (memoryOnly) return structuredClone(memory);
  try {
    return JSON.parse(window.localStorage.getItem(KEY) || "{}");
  } catch {
    return structuredClone(memory);
  }
}

function writeAll(data) {
  memory = structuredClone(data);
  try {
    window.localStorage.setItem(KEY, JSON.stringify(data));
  } catch {
    memoryOnly = true; // blocked or full: keep the in-memory copy for this visit
  }
}

export function getPref(name, fallback) {
  return readAll().prefs?.[name] ?? fallback;
}

export function setPref(name, value) {
  const data = readAll();
  data.prefs = { ...data.prefs, [name]: value };
  writeAll(data);
}

/** {sections: {"4.2": {done: true, quiz: 5, attempts: 2}}} */
export function get() {
  return { sections: readAll().sections ?? {} };
}

/** Save a quiz score; a section is done with 4 or more correct answers out of 5. */
export function save(sectionId, quizScore) {
  const data = readAll();
  const sections = data.sections ?? {};
  const old = sections[sectionId] ?? {};
  const best = Math.max(quizScore, old.quiz ?? 0);
  sections[sectionId] = { quiz: best, done: best >= 4, attempts: (old.attempts ?? 0) + 1 };
  data.sections = sections;
  writeAll(data);
}

/** The mock exam in progress or the last finished one (see exam.js), or null. */
export function getExam() {
  return readAll().exam ?? null;
}

export function setExam(state) {
  const data = readAll();
  data.exam = state;
  writeAll(data);
}
