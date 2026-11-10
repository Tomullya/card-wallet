# ISTQB Lab Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public, bilingual (RU/EN) ISTQB CTFL v4.0.1 trainer site — theory per learning objective with Card Wallet examples, terms, quizzes, technique trainers on real wallet rules, glossary and a 40-question mock exam.

**Architecture:** Static site in `site/istqb/` (plain HTML/CSS/ES modules, no build), shell copied from `site/grpc-lab/`. Learning content is data: `content/syllabus.json` (chapters → sections → LOs), `content/sections/<id>.json` (explanations, wallet examples, terms), `content/questions.json` (question bank), `content/comics.json`. Pure logic (`js/techniques.js`, `js/exam.js`, `js/wallet-rules.js`) is tested with Node; content integrity and "trainer numbers = wallet code" are tested with pytest; the UI with Playwright. CI copies the site into the Pages artifact under `istqb/`.

**Tech Stack:** HTML, CSS, JavaScript ES modules, inline SVG, Node 24 built-in test runner, pytest, pytest-playwright (existing), `pdftotext` (local, for reading the syllabus only).

**Spec:** `docs/design/2026-11-10-istqb-lab-design.md`

## Global Constraints

- No framework, bundler or npm dependency for the site; only Google Fonts as an external request.
- UI strings in `site/istqb/i18n/ru.json` and `en.json` (identical key sets); learning content in `content/*.json` with `{"ru": …, "en": …}` pairs; code holds no UI or content text.
- Syllabus: **CTFL v4.0.1** (EN PDF `https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf`); RU terms and LO quotes from the official RSTQB translation of v4.0. 6 chapters, 22 sections (1.1–1.5, 2.1–2.3, 3.1–3.2, 4.1–4.5, 5.1–5.5, 6.1–6.2).
- Copyright: only LO wording and short term definitions are quoted, each with "ISTQB CTFL Syllabus v4.0.1, §x.y"; all explanations, examples, comics and questions are original; official sample exams are linked, never reproduced or paraphrased. Footer disclaimer text exactly as spec §2.
- Both terms always shown side by side: in RU mode "русский термин (english term)", in EN mode "english term (русский термин)".
- Mock exam: 40 questions — chapters 1–6 = **8 / 6 / 4 / 11 / 9 / 2**; 60 minutes (option "+25 % for non-native language" = 75 min); pass mark **26**; no feedback until submit.
- Section done at quiz score ≥ 4/5.
- Wallet numbers used in trainers equal the code: fraud threshold `5000.00` (`fraud-service/fraud_service/rules.py: HIGH_AMOUNT_THRESHOLD`), amount `> 0` and `≤ 10000.00` (`wallet-api/app/schemas/common.py: Amount`), daily limit `1.00…10000.00`, default `1000.00` (`wallet-api/app/schemas/cards.py`), `MAX_FAILED_CVV_ATTEMPTS = 3` (`wallet-api/app/services/payments.py`), currencies EUR/USD/PLN, categories GROCERIES/ELECTRONICS/TRAVEL/RESTAURANTS/GAMBLING/OTHER, card states ACTIVE/BLOCKED/EXPIRED.
- Palette, fonts, characters, light/dark theme as gRPC Lab; original characters only.
- `localStorage` wrapped in try/catch with memory fallback (storage key `istqb-lab`).
- Keyboard-operable; contrast ≥ 4.5:1 both themes; `prefers-reduced-motion` respected.
- Every new pytest test carries `@pytest.mark.req(...)`; new requirements `NFR-11`, `NFR-12`.
- Commits authored as `Tomullya <61884339+Tomullya@users.noreply.github.com>`; no push without the author's OK.

## Review Focus

1. Russian users type decimals with a comma and spaces ("5 000,00") in trainers — must parse as 5000.00, and garbage ("abc") must show a clear message, not a wrong verdict — pinned in Task 3 (`parseAmount accepts comma and spaces`, `parseAmount rejects garbage`).
2. Switching language in the middle of the mock exam must keep answers and the timer — pinned in Task 11 (`test_language_switch_keeps_exam`).
3. Timer reaching zero auto-submits; unanswered questions count as wrong — pinned in Task 11 (`timeout submits and unanswered are wrong`).
4. Reloading the page during the mock exam resumes it with the remaining time instead of losing it — pinned in Task 11 (`resume restores answers and remaining time`).
5. A question whose RU and EN versions disagree (different option count, answer index out of range, "select TWO" with one answer) — pinned in Task 1 (`test_question_shape`).

---

### Task 1: Requirements, syllabus data and content checks

**Files:**
- Modify: `docs/requirements/NFR.md`
- Create: `site/istqb/content/syllabus.json`, `site/istqb/content/questions.json` (empty list `[]`), `site/istqb/content/sections/` (empty), `tests/unit/test_istqb_content.py`

**Interfaces:**
- Produces: `syllabus.json` = `{"version": "4.0.1", "links": {"en": url, "ru": url, "glossary": "https://glossary.istqb.org/", "samples": [{"name": "A", "url": …}, …D]}, "chapters": [{"id": "4", "minutes": 390, "title": {ru,en}, "sections": [{"id": "4.2", "title": {ru,en}, "los": [{"id": "FL-4.2.1", "k": "K3", "quote": {ru,en}}]}]}]}`
- Produces: question shape `{"id": "q-4.2.1-01", "section": "4.2", "lo": "FL-4.2.1", "k": "K3", "q": {ru,en}, "options": {"ru": [..], "en": [..]}, "answer": [int, …], "why": {ru,en}}` — `answer` has 1 item, or 2 for "select TWO" (then 5 options).
- Produces: section file shape `{"id": "4.2", "objectives": [{"lo": "FL-4.2.1", "explain": {"ru": [p…], "en": [p…]}, "wallet": {"ru": str, "en": str, "link": url|null}}], "terms": [{"ru": str, "en": str, "explain": {ru,en}}], "trainers": ["ep", "bva"]}` (`trainers` optional).

- [ ] **Step 1: Add NFR-11 (ISTQB trainer site: 6 chapters / 22 sections, RU+EN, theory+terms+quiz, trainers 4.2/4.3, glossary, mock exam 40/60/26, copyright rules) and NFR-12 (trainer rules equal wallet constants) to `docs/requirements/NFR.md`, same format as NFR-09/10.**
- [ ] **Step 2: Download the RU translation from RSTQB (ISTQB Materials page) into the scratchpad; extract LO lists from both PDFs with `pdftotext -layout`.** If the RU PDF cannot be fetched: Ruling — RU quotes are own translations marked "перевод автора", ledger it.
- [ ] **Step 3: Write `test_istqb_content.py` (all `@pytest.mark.req("NFR-11")`):**
  - `test_syllabus_shape`: 6 chapters, minutes `[180,130,80,390,335,20]`, section ids exactly the 22 above, every LO id matches `FL-\d\.\d\.\d`, `k in {K1,K2,K3}`, both quote languages non-empty, total LO count == the count read from the PDF in Step 2 (write the number as a constant with a comment naming the PDF).
  - `test_question_shape` (parametrized per question): LO and section exist in syllabus, `len(options.ru) == len(options.en)`, all answer indices in range, `len(answer)==2` iff 5 options, non-empty `q/why` both languages, ids unique.
  - `test_section_files` (parametrized per existing file in `content/sections/`): every LO of that section has an objective entry with ≥1 paragraph both languages and a wallet example; ≥3 terms.
  - `test_every_lo_has_two_questions` — marked `xfail(strict=False, reason="filled chapter by chapter")` until Task 10 removes the mark.
- [ ] **Step 4: Run `pytest tests/unit/test_istqb_content.py -v`.** Expected: FAIL (syllabus.json missing).
- [ ] **Step 5: Write `syllabus.json` from the two PDFs (titles, minutes, all LOs, EN and RU wording). Run again.** Expected: PASS (`xfail` for the two-questions test).
- [ ] **Step 6: Commit** `feat(istqb): requirements, syllabus data and content checks`.

### Task 2: Site shell

**Files:**
- Create: `site/istqb/index.html`, `css/site.css`, `js/app.js`, `js/i18n.js`, `js/progress.js`, `js/art.js`, `js/tabs.js`, `i18n/ru.json`, `i18n/en.json`
- Modify: `tests/e2e/conftest.py` (add `istqb_url` fixture, same server as `lab_url`, path `/istqb/index.html`), `tests/unit/test_site_i18n.py` (parametrize over both sites)
- Test: `tests/e2e/test_istqb_site.py`

**Interfaces:**
- Consumes: `syllabus.json` (Task 1).
- Produces: routes `#/` (home map), `#/ch/<n>` (chapter intro), `#/s/<section>/<tab>` with tabs `theory|terms|quiz|trainer` (`trainer` only when the section file lists trainers), `#/glossary`, `#/exam`. `registerTab(name, render)` / `registerPage(name, render)` with `ctx = {t, lang, progress, syllabus, section, rerender, refreshMenu}`. `progress.save(sectionId, score)`, `progress.get().sections`, `getPref/setPref`. `term(pair, lang) → "ru (en)" | "en (ru)"`. `loadSection(id) → Promise<section|null>` (cached fetch).

- [ ] **Step 1: Copy `i18n.js`, `progress.js` (key `istqb-lab`, `sections` instead of `lessons`), `art.js`, `tabs.js` and CSS from `site/grpc-lab/`; write `index.html` (rail: brand "ISTQB Lab", RU/EN, theme, chapter menu with sections and done marks, links Glossary/Exam; main; footer with disclaimer + syllabus version).**
- [ ] **Step 2: Write E2E tests (`@pytest.mark.req("NFR-11")`):** `test_menu_lists_chapters_and_sections` (6 chapters, 22 section links), `test_deep_link_opens_section_tab` (`#/s/4.2/terms`), `test_language_switch_keeps_place`, `test_theme_toggle`, `test_site_works_without_storage` (init script that makes `localStorage` throw), `test_footer_disclaimer`. Run → FAIL.
- [ ] **Step 3: Implement `app.js` routing/menu/home map (chapter cards with done/total) and placeholder tab bodies; `term()` helper in `i18n.js`. Extend `test_site_i18n.py` to both sites. Run E2E + unit.** Expected: PASS.
- [ ] **Step 4: Commit** `feat(istqb): site shell, routing, menu, themes`.

### Task 3: Wallet rules and technique checkers (pure logic)

**Files:**
- Create: `site/istqb/js/wallet-rules.js`, `site/istqb/js/techniques.js`, `site/istqb/tests/techniques.test.mjs`, `tests/unit/test_istqb_wallet_rules.py`

**Interfaces:**
- Produces `wallet-rules.js`: `RULES = {fraudThreshold: "5000.00", amountMin: "0.01", amountMax: "10000.00", dailyLimitMin: "1.00", dailyLimitMax: "10000.00", dailyLimitDefault: "1000.00", maxCvvAttempts: 3, currencies: [...], categories: [...], cardStates: ["ACTIVE","BLOCKED","EXPIRED"]}`; `fraudDecision(amount, category) → {decision, reason}`; `cardTransitions` = list of `{from, event, to}` (ACTIVE –wrong CVV ×3→ BLOCKED, ACTIVE –block by client→ BLOCKED, ACTIVE –expiry date passes→ EXPIRED, BLOCKED –expiry→ BLOCKED (blocked wins, per `effective_status`)).
- Produces `techniques.js` (amounts as cents integers internally):
  - `parseAmount(text) → {ok: true, cents} | {ok: false, error: "format"}` — accepts `5000`, `5000.5`, `5 000,00`, `-1`; rejects letters, >2 decimals.
  - `epCheck(task, values) → {covered: [partitionId], missing: [partitionId], duplicates: [[value, partitionId]], invalid: [text]}`; tasks `amount` (partitions `≤0`, `0.01–5000.00`, `5000.01–10000.00`, `>10000.00`) and `category` (6 valid + "other value").
  - `bvaCheck(task, values, variant: 2|3) → {required: [cents], covered: [...], missing: [...]}`; task `fraud` boundaries around 5000.00 (2-value: 5000.00, 5000.01; 3-value: 4999.99, 5000.00, 5000.01) and `amount` (0.00/0.01 … 10000.00/10000.01).
  - `decisionTable(rules) → {columns, missing, contradictions, minimised}` for conditions `amount > 5000.00`, `category = GAMBLING`.
  - `stateCoverage(transitions, testSteps) → {states: {covered, total}, valid: {covered, total}, invalid: {tried: [...]}}`.
  - `codeCoverage(program, inputs) → {statement: %, branch: %}` for a small fixed program model `{statements: [...], branches: [...]}` of `fraudDecision`.

- [ ] **Step 1: Write Node tests** — including `parseAmount accepts comma and spaces` (`"5 000,00"` → 500000), `parseAmount rejects garbage` (`"abc"`, `"1.234"`), EP for `[100, 6000, -5]` → missing `>10000.00`, duplicates for `[10, 20]`, BVA 2-value with `[5000, 5000.01]` → nothing missing, 3-value missing `4999.99`, decision table with 3 of 4 columns → 1 missing, a contradiction case, state coverage of `ACTIVE→BLOCKED` only → 2/3 states, statement 100 % but branch < 100 % for a single high-amount input. Run `node --test "site/istqb/tests/*.test.mjs"` → FAIL.
- [ ] **Step 2: Implement `wallet-rules.js` and `techniques.js`.** Run → PASS.
- [ ] **Step 3: Write `test_istqb_wallet_rules.py` (`@pytest.mark.req("NFR-12")`): reads `RULES` from `wallet-rules.js` (regex over the object literal) and compares with the Python constants imported from `fraud_service.rules`, `app.services.payments`, `app.schemas.common`/`cards` (read `Field` metadata), `app.models` enums. Change one JS number locally to see it FAIL, restore → PASS.**
- [ ] **Step 4: Commit** `feat(istqb): wallet rules and technique checkers`.

### Task 4: Section 4.2 end to end (first iteration for the author)

**Files:**
- Create: `site/istqb/content/sections/4.2.json`, `js/theory.js`, `js/terms.js`, `js/quiz.js`, `js/trainers.js`; questions for FL-4.2.1…4.2.4 in `questions.json` (≥ 3 each, ≥ 12 total)
- Modify: `i18n/*.json`, `tests/e2e/test_istqb_site.py`

**Interfaces:**
- Consumes: shell (Task 2), checkers (Task 3), shapes (Task 1).
- Produces: `pickQuiz(questions, sectionId, attempt) → 5 questions` (deterministic rotation by attempt, exported from `js/quiz.js`); trainer UI `renderTrainer(kind, ctx)` for `ep`, `bva` (others added in Task 5).

- [ ] **Step 1: E2E tests:** `test_theory_shows_lo_quote_and_wallet_example` (K-badge, "Source: … §4.2.1", wallet box, syllabus links EN+RU), `test_terms_show_both_languages`, `test_section_quiz_marks_done` (answer 5 → done mark in menu), `test_ep_trainer_reports_missing_partition`, `test_bva_trainer_variant_switch`. Run → FAIL.
- [ ] **Step 2: Write content for 4.2 (RU + EN): explanation per LO in plain words, wallet example per LO (EP: payment amount; BVA: 5000.00 and amount limits, mention BUG-02 "exact daily limit declined" from `docs/qa` with link; decision table: fraud rules; state transitions: card statuses), ≥ 6 terms, ≥ 12 questions incl. K3 calculation questions.**
- [ ] **Step 3: Implement theory/terms/quiz tabs and EP/BVA trainers. Run E2E + unit + node.** Expected: PASS.
- [ ] **Step 4: Fact review:** dispatch a reviewer subagent with the syllabus text of §4.2 and `4.2.json` + 4.2 questions: check every claim and every correct answer; fix findings; ledger them.
- [ ] **Step 5: Commit** `feat(istqb): section 4.2 with EP and BVA trainers`.
- [ ] **Step 6: CHECKPOINT — show the author section 4.2 locally (`python -m http.server` from `site/`) and collect feedback before Task 5.** This is the spec's "Done when #1"; apply feedback as rulings.

### Task 5: Remaining trainers (decision table, state transitions, coverage)

**Files:** Modify `js/trainers.js`, `content/sections/4.2.json` (`trainers`), create `content/sections/4.3.json` (content for 4.3 incl. `trainers: ["coverage"]`, questions ≥ 2 per LO); E2E tests.

- [ ] **Step 1: E2E:** `test_decision_table_trainer_finds_missing_column`, `test_state_trainer_counts_transitions`, `test_coverage_trainer_statement_vs_branch`. Run → FAIL.
- [ ] **Step 2: Implement the three trainer UIs (table with toggles; state diagram SVG with clickable transitions; code listing with highlighted executed lines/branches). Write 4.3 content and questions. Run all.** Expected: PASS.
- [ ] **Step 3: Fact review of 4.3 (as Task 4 Step 4). Commit** `feat(istqb): decision-table, state and coverage trainers; section 4.3`.

### Task 6: Chapter pages and comics

**Files:** Create `content/comics.json`, `js/comic.js` (copied/adapted from gRPC Lab), chapter intro page renderer; E2E `test_chapter_page_has_comic_and_objectives`.

- [ ] **Step 1: E2E test → FAIL. Step 2: six original 3–4-panel strips (ch1 error→defect→failure with the Gnome; ch2 levels as tower floors; ch3 review of a scroll before sending; ch4 owls choosing test values; ch5 planning the post route / defect report; ch6 enchanted tools), chapter intro: comic, minutes, list of sections with LO count and progress. Run → PASS. Step 3: Commit** `feat(istqb): chapter pages and comics`.

### Tasks 7–10: Content chapters

One task per group, same steps each: write `content/sections/<id>.json` for every section of the group (explanations per LO, wallet example per LO with a link to a real file/requirement/bug where one exists, ≥ 3 terms), questions ≥ 2 per LO with explanations; run `pytest tests/unit/test_istqb_content.py` (PASS); fact-review subagent pass against the syllabus text of those sections; fix; commit `feat(istqb): chapter N content`.

- [ ] **Task 7:** Chapter 1 (1.1–1.5). Wallet examples: BUG reports in `docs/qa` as error/defect/failure; traceability gate (`scripts/traceability.py`) for FL-1.4.4; roles in this project.
- [ ] **Task 8:** Chapters 2 and 3 (2.1–2.3, 3.1–3.2). Examples: unit/integration/E2E/gRPC tests as test levels; CI as DevOps/shift left; requirements review as static testing.
- [ ] **Task 9:** Chapter 4 rest (4.1, 4.4, 4.5). Examples: error guessing on `TEST_TIMEOUT`, exploratory charter for the wallet, checklist, user stories + acceptance criteria from `docs/requirements`.
- [ ] **Task 10:** Chapters 5 and 6 (5.1–5.5, 6.1–6.2). Examples: test plan elements for the wallet, risk analysis (payments vs statement), metrics from Allure, defect report template from `docs/qa`, tools used in the project. Remove the `xfail` from `test_every_lo_has_two_questions`; total questions ≥ 130. Run → PASS.

### Task 11: Glossary and mock exam

**Files:** Create `js/exam.js` (pure), `js/exam-page.js`, `js/glossary.js`, `site/istqb/tests/exam.test.mjs`; E2E tests.

**Interfaces:**
- Produces `exam.js`: `buildExam(questions, seed) → [questionId×40]` with per-chapter counts `{1:8,2:6,3:4,4:11,5:9,6:2}`, no duplicates, throws if the bank is too small; `score(exam, answers) → {total, passed, byChapter: {n: {right, of}}}` (pass ≥ 26; "select TWO" right only if both); `remaining(startedAt, now, minutes) → seconds`; `state` saved via `progress.setExam(state)` / `progress.getExam()`.

- [ ] **Step 1: Node tests:** distribution, no duplicates, deterministic for a seed, `score` pass at 26 and fail at 25, select-two partial = wrong, `timeout submits and unanswered are wrong`, `resume restores answers and remaining time`. Run → FAIL.
- [ ] **Step 2: E2E:** `test_glossary_search_both_languages` (search "граничн" and "boundary" find the same term), `test_mock_exam_full_run` (start → answer all → submit → score and per-chapter table → review shows explanations), `test_language_switch_keeps_exam`, `test_official_samples_links` (A–D link to istqb.org). Run → FAIL.
- [ ] **Step 3: Implement exam builder, exam page (start screen with 60/75 min choice, question navigator, timer, submit confirm, results, "retry wrong ones"), glossary (all terms from section files, search, link to glossary.istqb.org). Run all.** Expected: PASS.
- [ ] **Step 4: Commit** `feat(istqb): glossary and mock exam`.

### Task 12: Delivery

**Files:** Modify `scripts/ci_local.sh`, `README.md`, `docs/requirements/NFR.md` (if counts changed).

- [ ] **Step 1: `ci_local.sh`: node step runs `site/istqb/tests/*.test.mjs` too; after the gRPC Lab copy, copy `site/istqb/.` to `reports/allure-report/istqb/` and remove its `tests/`.**
- [ ] **Step 2: README: ISTQB Lab link next to gRPC Lab, test counts.**
- [ ] **Step 3: Run `scripts/ci_local.sh`.** Expected: ends with `CI OK`; `reports/allure-report/istqb/index.html` exists.
- [ ] **Step 4: Commit** `ci: publish ISTQB Lab next to the report`. Then final whole-branch review (opus), fixes by TDD, and ask the author for the push OK and a new token.
