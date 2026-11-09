# gRPC Lab Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public, bilingual (RU/EN), interactive gRPC trainer site — comic, theory, animated diagram, sandbox, quiz, practice per lesson — whose sandbox is proven equal to the real Fraud Service in CI.

**Architecture:** Static site in `site/grpc-lab/` (plain HTML/CSS/ES modules, no build). A pure simulator `js/sim.js` and a shared `scenarios.json` are tested twice: by Node against the simulator and by pytest against the real gRPC service. UI modules render lessons from `content/lessons.json` + `i18n/{ru,en}.json`. CI copies the site into the Pages artifact under `grpc-lab/`.

**Tech Stack:** HTML, CSS, JavaScript ES modules, inline SVG, Node 24 built-in test runner, pytest + grpcio, pytest-playwright (existing).

**Spec:** `docs/design/2026-11-09-grpc-lab-site-design.md`

## Global Constraints

- No framework, no bundler, no npm dependencies for the site; only Google Fonts as an external request.
- All UI text lives in `site/grpc-lab/i18n/ru.json` and `en.json` with identical key sets; code holds no UI strings.
- Palette: navy `#15233B`, accent `#C9551C`, light background `#F7F5F0`; dark theme via `[data-theme="dark"]` and `prefers-color-scheme`.
- Original characters only (Mage-Treasurer, Master-Inspector, Mage-Watcher, Gnome-Trickster, owls); nothing from existing franchises.
- Simulator constants equal the service: threshold `5000.00`, `MAX_BATCH` 1000, watchers 8, `MAX_STREAMS` 16, `TEST_TIMEOUT` 5 s, keys `dev-wallet-key` / `dev-monitor-key`.
- `localStorage` access wrapped in try/catch; the site works without it.
- Respect `prefers-reduced-motion`; keyboard-operable tabs, buttons and presets; contrast ≥ 4.5:1 in both themes.
- Every new pytest test carries `@pytest.mark.req(...)`; new requirements `NFR-09`, `NFR-10`.
- Lesson facts must match `docs/grpc-lab/*.md` (source of truth).

## Review Focus

1. A scenario that passes in the simulator but has no counterpart run against the real service (simulator drift) — pinned in Task 2 (`test_every_scenario_runs_against_service`: every id in `scenarios.json` is executed by pytest).
2. Switching language mid-lesson must keep the current lesson and tab — pinned in Task 3 (`test_language_switch_keeps_place`).
3. Private/blocked storage must not break the site — pinned in Task 3 (`test_site_works_without_storage`).
4. Stream sandbox with "cancel" before any owl is sent must end with `CANCELLED`, not hang — pinned in Task 1 (`bidi cancel before first message`).
5. Reduced-motion users must still see the final state of animations — pinned in Task 4 (`test_reduced_motion_shows_final_state`).

---

### Task 1: Requirements, scenarios and the simulator

**Files:**
- Modify: `docs/requirements/NFR.md`
- Create: `site/grpc-lab/scenarios.json`, `site/grpc-lab/js/sim.js`, `site/grpc-lab/tests/sim.test.mjs`

**Interfaces:**
- Produces scenario shape (JSON):
  `{"id": str, "lesson": "05", "method": "CheckPayment"|"GetDecision"|"WatchRiskEvents"|"CheckBatch"|"ScorePayments", "seal": "wallet"|"monitor"|"forged"|null, "requestId": str|null, "deadline": number (s), "payments": [{"amount","category","merchant"}], "minRiskScore": int, "batchSize": int (generated payments, overrides payments), "openWatchers": int, "openStreams": int, "unknownTransaction": bool, "clientAction": "finish"|"cancel", "buggy": bool, "expect": {"code": str, "decisions": [str], "reasons": [str], "riskScores": [int], "summary": {"total","approved","declined"}, "trailerRequestId": str|"generated"|"absent"}}` — omitted keys = defaults (seal wallet, deadline 2, one default payment 10.00 GROCERIES Shop, clientAction finish, buggy false).
- Produces `sim.js`: `export function run(scenario) -> Result` with `Result = {code: str, number: int, details: str, timeline: [{t: number, dir: "out"|"in"|"end", label: str, body: object}], trailers: {"x-request-id"?: str}, answers: [object], summary?: object}`; `export const CODES` (name → number); `export const LIMITS`.

- [ ] **Step 1: NFR-09 / NFR-10** in `docs/requirements/NFR.md`: NFR-09 "Interactive bilingual trainer site" (acceptance: spec §2–§5 bullets, 9 lessons, RU/EN complete); NFR-10 "Sandbox matches the service" (every scenario passes against both).
- [ ] **Step 2: scenarios.json** — at least these ids (lesson 05 first, others for later lessons): `unary-approve`, `unary-boundary-5000`, `unary-high-amount`, `unary-gambling`, `no-seal`, `forged-seal`, `monitor-pays`, `amount-abc`, `test-error`, `slow-deadline-1s`, `slow-deadline-7s`, `lookup-unknown`, `watch-sees-payment`, `watch-filter-50`, `watch-score-101`, `ninth-watcher`, `watch-cancel`, `batch-totals`, `batch-empty`, `batch-1001`, `batch-bad-item`, `bidi-order`, `bidi-bad-item`, `bidi-cancel-first`, `seventeenth-stream`, `request-id-echo`, and `buggy: true` ones `bug17-forged-seal`, `bug18-bidi-hangs`, `bug19-no-trailer` with the buggy expectations (`PERMISSION_DENIED`, `DEADLINE_EXCEEDED`, `absent`).
- [ ] **Step 3: Node test** `tests/sim.test.mjs`: loads `scenarios.json`, for each scenario `run(s)` and asserts `code` plus every present `expect` field; plus named tests `bidi cancel before first message` (→ `CANCELLED`, 0 answers) and `timeline is time-ordered` (non-decreasing `t`).
- [ ] **Step 4: Run** `node --test site/grpc-lab/tests` → FAIL (module missing).
- [ ] **Step 5: Implement `sim.js`** mirroring `fraud-service/fraud_service/server.py` order: auth (missing/forged → `UNAUTHENTICATED`, buggy forged → `PERMISSION_DENIED`; monitor on non-monitor method → `PERMISSION_DENIED`) → method rules → `TEST_ERROR` `INTERNAL` → `TEST_TIMEOUT` vs deadline → amount validation (index in details) → rules. Trailers: `x-request-id` = sent or `"generated"` marker UUID, absent in buggy mode on non-auth outcomes. Simulated clock, no waiting.
- [ ] **Step 6: Run** → PASS. **Step 7:** Commit `feat(site): simulator and shared sandbox scenarios`.

### Task 2: Scenarios against the real service

**Files:** Create `tests/grpc/test_sandbox_scenarios.py`

**Interfaces:** Consumes `scenarios.json` (Task 1); reuses `tests/grpc_helpers.Watcher`, `tests/grpc/test_limits.IdleStream`.

- [ ] **Step 1: Tests** (`@pytest.mark.req("NFR-10")`): `test_scenario[<id>]` parametrized over non-buggy scenarios — builds the real call from the scenario (opens `openWatchers` / `openStreams` first, closes them in `finally`), asserts the same `expect` fields; `test_buggy_scenario[<id>]` over `buggy` ones against `localhost:50052` (skip with a clear message only if :50052 is down — CI starts it); `test_every_scenario_runs_against_service` asserts the parametrized ids cover all ids in the file.
- [ ] **Step 2: Run** `.venv/bin/pytest tests/grpc/test_sandbox_scenarios.py -q` → expect PASS for scenarios (service exists); any FAIL is a simulator/scenario error to fix in Task 1 files, not in the service.
- [ ] **Step 3:** Commit `test(site): sandbox scenarios run against the real Fraud Service`.

### Task 3: Site shell — layout, i18n, themes, progress, routing

**Files:**
- Create: `site/grpc-lab/index.html`, `css/site.css`, `js/app.js`, `js/i18n.js`, `js/progress.js`, `content/lessons.json`, `i18n/ru.json`, `i18n/en.json`
- Create: `tests/e2e/test_grpc_lab_site.py`, `tests/unit/test_site_i18n.py`; Modify `tests/e2e/conftest.py`

**Interfaces:**
- Produces routes `#/<lesson>/<tab>` with lesson `00`–`08`, tab `comic|theory|diagram|sandbox|quiz|practice`; default `#/00/comic`.
- Produces `i18n.t(key, vars?) -> str`, `i18n.setLang("ru"|"en")`; `progress.get() -> {lessons: {"05": {done: bool, quiz: int}}}`, `progress.save(lessonId, quizScore)`.
- Produces `lessons.json`: `[{"id": "05", "callType": "server"|"unary"|"client"|"bidi"|null, "presets": [scenario ids], "quiz": [{"q": key, "options": [keys], "answer": index, "why": key}], "comic": [{"scene": str, "speaker": character, "text": key, "caption"?: key}], "practice": {"check": "N"|null, "files": [paths]}}]`.
- Produces E2E fixture `lab_url` (serves `site/` with `python -m http.server` on a free port for the session) and test-id attributes `data-testid="lesson-05"`, `tab-sandbox`, `lang-en`, `theme-toggle`, `lesson-done-05`.

- [ ] **Step 1: Unit test** `test_site_i18n.py` (NFR-09): same key sets, no empty values, every key referenced in `lessons.json` exists. **Run** → FAIL.
- [ ] **Step 2: E2E tests** (NFR-09): `test_menu_lists_nine_lessons`, `test_tabs_switch_content`, `test_language_switch_keeps_place` (on `#/05/quiz` switch to EN → same route, English heading), `test_theme_toggle_persists`, `test_site_works_without_storage` (context with `localStorage` throwing via init script → page renders, no console errors), `test_deep_link_opens_tab`. **Run** → FAIL.
- [ ] **Step 3: Implement** shell per spec §2 (menu, toggles, tab bar, placeholder tab bodies), minimal i18n for all nine lesson titles. **Run** unit + E2E → PASS.
- [ ] **Step 4:** Commit `feat(site): shell with menu, tabs, RU/EN, themes and progress`.

### Task 4: Art kit and call-type diagrams

**Files:** Create `site/grpc-lab/js/art.js`, `js/comic.js`, `js/diagram.js`; extend `tests/e2e/test_grpc_lab_site.py`

**Interfaces:**
- Produces `art.character(name: "treasurer"|"inspector"|"watcher"|"gnome"|"owl", pose: "idle"|"ask"|"happy"|"panic"|"stern"|"sneaky") -> SVG string` (each with `aria-label`).
- Produces `comic.render(panels, t) -> HTMLElement`; `diagram.render(callType, t) -> HTMLElement` with a replay button (`data-testid="diagram-replay"`).

- [ ] **Step 1: E2E** `test_comic_has_panels_and_bubbles` (≥ 3 panels, every bubble non-empty, every SVG has `aria-label`), `test_diagram_plays_for_each_call_type`, `test_reduced_motion_shows_final_state` (emulate reduced motion → final owl position/state visible without waiting). **Run** → FAIL.
- [ ] **Step 2: Implement** characters (reusable SVG, comic outline 3px navy, halftone background via CSS radial-gradient) and diagrams (unary: one owl there and back; server: one request, flock back; client: flock out, one owl back; bidi: alternating). **Run** → PASS.
- [ ] **Step 3:** Commit `feat(site): characters, comic panels and call-type diagrams`.

### Task 5: Lesson 05 end to end — then show the author

**Files:** Create `site/grpc-lab/js/sandbox.js`, `js/quiz.js`, `js/practice.js`; content for lesson 05 in `lessons.json`, `ru.json`, `en.json`; extend E2E

**Interfaces:** Consumes `sim.run`, `scenarios.json` (presets by id), `art`, `comic`, `diagram`, `progress`.

- [ ] **Step 1: E2E** (NFR-09, NFR-10): `test_sandbox_presets_show_expected_rune[<preset id>]` for every lesson-05 preset (rune text = scenario `expect.code`), `test_sandbox_timeline_rows` (watch-sees-payment shows the request row and an event row), `test_sandbox_code_view_toggle` (Postman / Python text contains method name and metadata key), `test_quiz_scoring_marks_lesson_done` (answer 5/5 → menu shows done mark after reload), `test_quiz_explains_wrong_answer`. **Run** → FAIL.
- [ ] **Step 2: Implement** sandbox (form + timeline + presets + rune + character reaction + code view), quiz (5 questions, explanation per answer, score ≥ 4 → done), practice tab (Postman steps, `grpc_lab_check.py 5`, GitHub links), lesson 05 comic and theory RU/EN from `docs/grpc-lab/05-server-streaming.md`. **Run** all site tests → PASS.
- [ ] **Step 3:** Commit `feat(site): lesson 05 complete`.
- [ ] **Step 4: STOP — author review.** Serve the site locally, open `#/05/comic` in the user's browser, collect feedback. Apply requested changes (each with an E2E/unit check where behaviour changes), commit `fix(site): lesson 05 feedback`. Only then continue.

### Task 6: Lessons 00–04

**Files:** content in `lessons.json`, `ru.json`, `en.json`; presets referencing Task 1 scenarios

- [ ] **Step 1: E2E** parametrized over lessons 00–04: every tab renders non-empty in RU and EN; every preset shows its expected rune; quiz has 5 questions. **Run** → FAIL.
- [ ] **Step 2:** Write content from `docs/grpc-lab/00…04` (00: sandbox compares the same payment as JSON vs protobuf bytes and field numbers; no stream controls). **Run** → PASS. **Step 3:** Commit `feat(site): lessons 00-04`.

### Task 7: Lessons 06–08 (incl. bug hunt)

**Files:** as Task 6; `sandbox.js` gains a "fraud-buggy :50052" switch used only in lesson 08

- [ ] **Step 1: E2E** as Task 6 for 06–08, plus `test_bug_hunt_switch_reveals_bugs` (lesson 08: presets `bug17…bug19` show the buggy runes only with the switch on). **Run** → FAIL.
- [ ] **Step 2:** Content from `docs/grpc-lab/06…08`; lesson 08 sandbox with the buggy switch and the Gnome-Trickster. **Run** → PASS. **Step 3:** Commit `feat(site): lessons 06-08 and bug hunt`.

### Task 8: CI, Pages, README

**Files:** Modify `scripts/ci_local.sh`, `.github/workflows/ci.yml`, `README.md`, `docs/grpc-lab/README.md`, `docs/qa/traceability-matrix.md` (regenerated)

- [ ] **Step 1:** `ci_local.sh`: step "gRPC Lab site: simulator tests" → `node --test site/grpc-lab/tests`; the pytest step already collects the new tests; after the Allure step `mkdir -p reports/allure-report/grpc-lab && cp -R site/grpc-lab/. reports/allure-report/grpc-lab/` (exclude `tests/`).
- [ ] **Step 2:** README: row "Interactive gRPC trainer (RU/EN)" → `https://tomullya.github.io/card-wallet/grpc-lab/`; counts updated from `pytest --collect-only -q`; lesson README links to the site.
- [ ] **Step 3: Run** `scripts/ci_local.sh` → ends `CI OK`; check `reports/allure-report/grpc-lab/index.html` exists. **Step 4:** Commit `ci: publish gRPC Lab site next to the Allure report`.
- [ ] **Step 5:** Final whole-branch review → fix Important → merge to `main` and push only with the user's OK → open the public URL and confirm it loads.
