// Mock exam logic. Pure functions, no DOM: the state is a plain object that can be saved in
// localStorage and resumed later.
// state = {seed, ids, answers: {id: [index…]}, startedAt, minutes, submitted, submittedAt, result}

export const DISTRIBUTION = { 1: 8, 2: 6, 3: 4, 4: 11, 5: 9, 6: 2 }; // questions per chapter
export const PASS_MARK = 26; // of 40 (65 %)
export const MINUTES = 60;
export const MINUTES_EXTENDED = 75; // +25 % for an exam in a non-native language

const chapterOf = (q) => q.section.split(".")[0];
const isExam = (q) => q.exam !== false;

/** Small seeded random generator (mulberry32), so an exam can be rebuilt from its seed. */
function random(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffle(list, rnd) {
  const a = [...list];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** 40 question ids, chapter by chapter; throws if a chapter has too few exam questions. */
export function buildExam(questions, seed) {
  const rnd = random(seed);
  const short = [];
  const ids = [];
  for (const [chapter, n] of Object.entries(DISTRIBUTION)) {
    const pool = questions.filter((q) => isExam(q) && chapterOf(q) === chapter).map((q) => q.id).sort();
    if (pool.length < n) short.push(`chapter ${chapter}: ${pool.length} of ${n}`);
    ids.push(...shuffle(pool, rnd).slice(0, n));
  }
  if (short.length) throw new Error(`question bank too small (${short.join("; ")})`);
  return ids;
}

/** Right only if exactly the correct options were chosen. */
export function isRight(question, chosen) {
  if (!chosen?.length || chosen.length !== question.answer.length) return false;
  return question.answer.every((a) => chosen.includes(a));
}

export function score(ids, answers, questions) {
  const byId = new Map(questions.map((q) => [q.id, q]));
  const byChapter = {};
  let total = 0;
  for (const id of ids) {
    const q = byId.get(id);
    const ch = chapterOf(q);
    byChapter[ch] ??= { right: 0, of: 0 };
    byChapter[ch].of += 1;
    if (isRight(q, answers[id])) {
      byChapter[ch].right += 1;
      total += 1;
    }
  }
  return { total, of: ids.length, passed: total >= PASS_MARK, byChapter };
}

export function startExam(questions, { seed, now, minutes = MINUTES }) {
  return { seed, ids: buildExam(questions, seed), answers: {}, startedAt: now, minutes, submitted: false };
}

export function answer(state, id, indices) {
  if (state.submitted) return state;
  return { ...state, answers: { ...state.answers, [id]: indices } };
}

/** Seconds left (0 when the time is over or the exam was submitted). */
export function remaining(state, now) {
  if (state.submitted) return 0;
  const end = state.startedAt + state.minutes * 60 * 1000;
  return Math.max(0, Math.ceil((end - now) / 1000));
}

export function submit(state, questions, now) {
  if (state.submitted) return state;
  const end = state.startedAt + state.minutes * 60 * 1000;
  return { ...state, submitted: true, submittedAt: Math.min(now, end), result: score(state.ids, state.answers, questions) };
}

/** A saved exam after a reload: still running, or submitted automatically if the time ran out. */
export function resume(state, questions, now) {
  return !state.submitted && remaining(state, now) === 0 ? submit(state, questions, now) : state;
}
