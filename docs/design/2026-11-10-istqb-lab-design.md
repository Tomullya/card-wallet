# ISTQB Lab (CTFL v4.0) trainer site — design

Date: 2026-11-10 · Status: agreed in conversation, awaiting the author's review of this document.
Sister site of the gRPC Lab (`docs/design/2026-11-09-grpc-lab-site-design.md`).

## 1. Goal

A public, bilingual (RU/EN) site that helps the author **understand the ISTQB Certified Tester
Foundation Level theory** and later prepare for the real exam, with every topic explained on the
Card Wallet project. It is also a portfolio piece next to the gRPC Lab.

- Public URL: `https://tomullya.github.io/card-wallet/istqb/`
- Source of truth: **CTFL syllabus v4.0.1** (ISTQB, 15 Sep 2024; the exam is still called
  "CTFL v4.0"). Russian terms follow the official RSTQB translation of v4.0 and the ISTQB Glossary.
- First priority: understanding. The mock exam comes after all chapters are in place.

Out of scope: accounts and server-side state, payments, Advanced Level, copying official sample
exams, mobile-first design (must work on a phone; target is a laptop).

## 2. Copyright rules (binding)

The syllabus allows short extracts for non-commercial use with the source named; any other use
needs written ISTQB approval.

- Allowed on the site: learning-objective wording (e.g. "FL-4.2.1 (K3) Use equivalence
  partitioning to derive test cases") and short term definitions, each marked as a quote with
  "Source: ISTQB CTFL Syllabus v4.0.1, §x.y" (or the Glossary).
- Everything else — explanations, examples, comics, questions — is written by us.
- Official sample exams A–D: links only, never reproduced or paraphrased question-by-question.
- Footer on every page: "ISTQB® is a registered trademark of the ISTQB. This site is an
  independent study aid, not affiliated with or endorsed by ISTQB/RSTQB."

## 3. Structure

```
Home (progress map of 6 chapters)
├── Chapter 1–6 intro page: comic strip + what you will learn + minutes in syllabus
│   └── Section page (1.1 … 6.2, 22 sections), tabs:
│       Теория/Theory · Термины/Terms · Квиз/Quiz · [Тренажёр/Trainer — only 4.2 and 4.3]
├── Glossary (all terms, RU↔EN search)
└── Exam: mock exam + links to official sample exams
```

Section tabs:

| Tab | Content |
|---|---|
| Theory | per learning objective: quoted LO with K-level badge → own explanation in plain words → **"In Card Wallet"** box with a concrete example (link to the real file / requirement / bug on GitHub where one exists) → "Read in the syllabus: §x.y" link (EN PDF and RU PDF) |
| Terms | the section's keywords: RU term, EN term, own one-line explanation, link to glossary.istqb.org |
| Quiz | 5 own questions for this section; explanation after each answer (Master-Inspector); section done at ≥ 4/5 |
| Trainer | interactive technique practice on wallet data (§5) |

The author does not know yet which exam language she will choose, so **both terms are always
shown side by side**, e.g. "Разбиение на классы эквивалентности (equivalence partitioning)".

## 4. World and look

Same "Academy of Magical Post" world, palette, fonts, light/dark theme and RU/EN switch as the
gRPC Lab, so both sites read as one series. Original characters only.

- Master-Inspector = the examiner / explains answers.
- Mage-Treasurer = developer of the wallet; Gnome-Trickster = defects (error → defect → failure).
- Owls = test cases / messages; one comic strip (3–4 panels) per chapter, six in total.

Shared code is **copied** from `site/grpc-lab` (art, i18n, progress, theme CSS) rather than
shared, so neither site can break the other; small duplication is accepted.

## 5. Technique trainers (chapter 4, K3 objectives)

Each trainer gives a task on real wallet rules, lets the author enter test values / fill a table,
and checks the answer with a pure-function checker (`js/techniques.js`, no DOM).

| Section | Task (wallet rule) | Checker reports |
|---|---|---|
| 4.2.1 Equivalence partitioning | payment amount (≤ 0, valid, above the daily limit); currency EUR/USD/PLN/other | which partitions are covered, which are missing, duplicates |
| 4.2.2 Boundary value analysis | Fraud rule boundary 5000.00, daily limit; 2-value and 3-value BVA | which boundary values are covered for the chosen variant |
| 4.2.3 Decision tables | fraud decision (amount > 5000.00, category `GAMBLING`) and payment checks order | missing / contradictory columns, minimised table |
| 4.2.4 State transitions | card: ACTIVE → BLOCKED (3 wrong CVV or by client), EXPIRED (by date) | coverage of states / valid transitions / invalid transitions |
| 4.3.1–4.3.2 Statement / branch | a short wallet function in pseudo-code | statement % and branch % for the chosen tests |

The rules shown must match the wallet code (`wallet-api/app/services/*`,
`fraud-service/fraud_service/server.py`); a test pins each number used (5000.00, 3 attempts,
currencies) to the code.

## 6. Question bank and mock exam

- Questions live in `site/istqb/content/questions.json`: id, section, LO id, K-level, RU and EN
  text, 4 options, exactly one correct (multi-answer allowed only where the real exam uses
  "select TWO"), explanation, syllabus reference.
- Target ≥ 130 own questions; every LO has at least 2.
- **Mock exam:** 40 questions, 60 minutes, distribution by chapter per the official exam
  structure (to be verified against the ISTQB Exam Structure Rules before implementation;
  expected 8 / 6 / 4 / 11 / 9 / 2), pass mark 26/40 (65 %). No feedback until the end; then score,
  score per chapter, review of mistakes with explanations, "retry wrong ones".
- Separate block "Official sample exams A–D" with links to the ISTQB PDFs.

## 7. Technology

`site/istqb/`: plain HTML + CSS + ES modules, no build step, like the gRPC Lab. Texts in
`i18n/ru.json` / `en.json`; lesson content in `content/*.json` (RU and EN side by side).
Progress and exam history in `localStorage` with a memory fallback. Routing `#/<section>/<tab>`.

## 8. Testing

1. **Node unit tests** (`site/istqb/tests/*.test.mjs`): technique checkers, exam builder
   (distribution, no duplicates, timer, scoring, pass mark), progress storage.
2. **Content checks** (pytest, `tests/unit/test_istqb_content.py`): every LO of the syllabus has
   an explanation, a wallet example and ≥ 2 questions; each question has one valid answer index,
   both languages, a section and LO that exist; RU/EN key sets equal; wallet numbers in trainers
   equal the constants in the code.
3. **Browser E2E** (`tests/e2e/test_istqb_site.py`, Playwright): language and theme switch,
   navigation, a section quiz, one trainer, start → finish mock exam with score per chapter,
   progress survives reload.
4. **Fact review:** after each chapter a separate reviewer pass checks explanations and answers
   against the syllabus PDF; wrong facts are the main risk of this project.
5. New requirements `NFR-11` (ISTQB site) and `NFR-12` (trainer rules match the wallet code) in
   `docs/requirements/NFR.md`; tests carry requirement tags as in the rest of the project.

## 9. Delivery

- `scripts/ci_local.sh` and the workflow run the new tests and copy `site/istqb/` to
  `reports/allure-report/istqb/` for the Pages artifact.
- README: link to the site next to the gRPC Lab.
- Order: **section 4.2 end to end first** (theory, terms, quiz, EP and BVA trainers) shown to the
  author; then the shell for all chapters; chapters 1–6; glossary; mock exam last.
- Push only with the author's OK and a new GitHub token.

## 10. Risks

| Risk | Mitigation |
|---|---|
| Wrong facts or wrong "correct" answers | quote LO, link exact section, reviewer pass per chapter, explanation cites §x.y |
| Copyright | §2 rules; footer disclaimer; no sample-exam content |
| Trainer rules drift from wallet code | content test pins numbers to code constants |
| Volume of content (22 sections × 2 languages) | one chapter at a time, content in JSON, author reviews RU |
| Syllabus changes | version shown in the footer; one file holds LO list |

## 11. Done when

1. Section 4.2 approved by the author after the first iteration.
2. All 22 sections with theory, terms and quiz in RU and EN; trainers for 4.2 and 4.3.
3. Glossary and mock exam work; ≥ 130 questions; every LO covered.
4. `scripts/ci_local.sh` ends with "CI OK" including the new tests.
5. After push, `https://tomullya.github.io/card-wallet/istqb/` opens and the README links to it.
