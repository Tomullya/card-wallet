// Preferences and lesson progress, kept in the browser. Works without storage (memory only).

const KEY = "grpc-lab";
const memory = {};

function readAll() {
  try {
    return JSON.parse(window.localStorage.getItem(KEY) || "{}");
  } catch {
    return { ...memory };
  }
}

function writeAll(data) {
  Object.assign(memory, data);
  try {
    window.localStorage.setItem(KEY, JSON.stringify(data));
  } catch {
    /* storage blocked: keep the in-memory copy for this visit */
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

/** {lessons: {"05": {done: true, quiz: 5}}} */
export function get() {
  return { lessons: readAll().lessons ?? {} };
}

/** Save a quiz score; a lesson is done with 4 or more correct answers out of 5. */
export function save(lessonId, quizScore) {
  const data = readAll();
  const lessons = data.lessons ?? {};
  const best = Math.max(quizScore, lessons[lessonId]?.quiz ?? 0);
  lessons[lessonId] = { quiz: best, done: best >= 4 };
  data.lessons = lessons;
  writeAll(data);
}
