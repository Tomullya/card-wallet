# gRPC Lab interactive site — design

Date: 2026-11-09 · Status: approved in conversation (look, structure, tech, testing), awaiting
review of this document. Builds on `docs/design/2026-11-09-grpc-deep-dive-design.md`.

## 1. Goal

Turn the Markdown lessons in `docs/grpc-lab/` into a public, interactive, bilingual (RU/EN)
trainer site that (a) the author uses to learn gRPC every day and (b) employers can open from the
README as part of the portfolio.

Public URL: `https://tomullya.github.io/card-wallet/grpc-lab/` (next to the Allure report).

Success = everything in §9 is true.

Out of scope: real gRPC calls from the browser (browsers cannot speak gRPC without a proxy —
that is what Postman and the exercises are for), accounts / login / server-side state,
analytics, a mobile-first design (must work on a phone, but the target is a laptop).

## 2. Look and feel (chosen with mockups)

- **Layout:** course app — left menu with lessons 00–08 and progress checkmarks; RU/EN switch;
  light/dark theme switch. Each lesson has six tabs: **Комикс / Comic, Теория / Theory,
  Схема / Diagram, Песочница / Sandbox, Квиз / Quiz, Практика / Practice**.
- **Theme:** light "fintech" by default (warm off-white, navy `#15233B`, accent orange
  `#C9551C`), dark theme toggle; same palette as the learning-plan deck.
- **World:** "Academy of Magical Post", comic style (thick outlines, halftone dots, speech
  bubbles, caption plates). Original characters only — nothing from existing franchises.

| Character | Plays | Notes |
|---|---|---|
| Mage-Treasurer | Wallet API (client) | sends owls, worries about deadlines |
| Master-Inspector | Fraud Service | crystal ball; answers in status-code runes |
| Mage-Watcher | Monitor role | tower; may only watch (`PERMISSION_DENIED` when paying) |
| Gnome-Trickster | attacker / planted bugs | villain of lesson 08 |
| Post owls | messages | one owl = one message, a flock = a stream |

Metaphors used consistently: scroll = protobuf message, wax seal = `x-api-key`, hourglass =
deadline, rune = status code, letter in the owl's last trip = trailers.

## 3. Lesson content

Nine lessons, same topics and facts as `docs/grpc-lab/00…08` (the Markdown stays the source of
truth for facts; the site may shorten wording). Per lesson:

| Tab | Content |
|---|---|
| Comic | one strip of 3–4 panels acting out the topic |
| Theory | the lesson text, RU and EN |
| Diagram | animated owl flight for the lesson's call type (unary / server / client / bidi stream) |
| Sandbox | §4; lessons 00 and 08 use a reduced sandbox (00: compare REST vs gRPC message; 08: bug hunt against a simulated buggy service) |
| Quiz | 5 questions; after each answer an explanation from the Master-Inspector |
| Practice | Postman steps, the exercise check command, links to files on GitHub |

A lesson counts as done when its quiz score is ≥ 4/5. Progress and quiz results are kept in the
browser (`localStorage`, wrapped in try/catch; the site works without it).

## 4. Sandbox

Layout B (chosen): call form on top, **time line** below — one row per message with a time
stamp, direction arrow, payload summary and the final status rune with trailers.

- Form: method, seal (none / wallet / monitor / forged), `x-request-id`, amount, category,
  merchant (`Shop`, `TEST_TIMEOUT`, `TEST_ERROR`), deadline (hourglass slider, 0.5–8 s);
  for streams: "another owl", "finish sending", "cancel" buttons; for `CheckBatch` a batch size.
- **"Break it" presets:** no seal; monitor seal on `CheckPayment`; amount `abc`;
  `TEST_TIMEOUT` with a 1 s deadline; empty batch; 1001-item batch; 9th watcher; 17th open
  stream; unknown transaction in `GetDecision`; `min_risk_score` 101.
- Result: rune with code name and number, one line "what it means / may the client retry",
  character reaction, a "Show as Postman / Python" toggle with the equivalent call.
- **Simulator** (`sim.js`, pure functions, no DOM): reproduces the real service rules from
  `fraud-service/fraud_service/` — decision rules (5000.00 boundary, `GAMBLING`), roles,
  request-id trailers, limits 1000 / 8 / 16, test merchants, deadline vs 5 s `TEST_TIMEOUT`,
  all-or-nothing batch, bidi ordering. Simulated time, no real waiting longer than the animation.

## 5. Technology

- `site/grpc-lab/`: plain HTML + CSS + JavaScript ES modules, no framework, no build step.
- Texts in `site/grpc-lab/i18n/ru.json` and `en.json` (same keys); code never contains UI text.
- Art: inline SVG components (characters, panels, owls), one file per character reused across
  panels; animations with CSS / Web Animations API; respects `prefers-reduced-motion`.
- Fonts from Google Fonts with system fallbacks; no other external requests.
- Accessible: keyboard navigation for tabs and sandbox, `aria-label`s on SVG, contrast ≥ 4.5:1
  in both themes.

## 6. Testing

1. **Simulator = real service.** `site/grpc-lab/scenarios.json` lists scenarios (request(s),
   metadata, deadline → expected status code and key response fields). The same file is run:
   - against the simulator with Node's built-in test runner (`node --test site/grpc-lab/tests`);
   - against the real Fraud Service by `tests/grpc/test_sandbox_scenarios.py` (pytest, gRPC).
   A mismatch fails CI. Every "Break it" preset is a scenario. Scenarios marked `buggy` (the
   lesson 08 bug hunt: BUG-17…19) run against the simulator in buggy mode and against
   `fraud-buggy` on :50052.
2. **Browser E2E** (`tests/e2e/test_grpc_lab_site.py`, Playwright, existing setup): the site is
   served locally; checks RU/EN switch, theme switch, lesson navigation, each preset shows the
   expected rune, quiz scoring, progress survives reload.
3. **Translation completeness:** a unit test asserts `ru.json` and `en.json` have identical key
   sets and no empty values.
4. Every new test carries a requirement tag; new requirements `NFR-09` (trainer site) and
   `NFR-10` (simulator matches the service) go into `docs/requirements/NFR.md`.

## 7. Delivery

- CI (`scripts/ci_local.sh` + workflow) runs the new tests and copies `site/grpc-lab/` into
  `reports/allure-report/grpc-lab/` before the Pages upload, so one Pages artifact serves both.
- README: link to the site in the "What this project demonstrates" table and a badge-row link.
- Order of work: **lesson 05 end to end first** (comic, all tabs, sandbox with streams), shown to
  the author for feedback; then the shell for all lessons and lessons 00–04, 06–08.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Simulator drifts from the real service | shared `scenarios.json` run against both in CI |
| Art takes too long | characters drawn once as reusable SVG; strips reuse poses |
| Translation quality | author reviews RU; EN written plainly; key-set test catches gaps |
| Pages artifact path collides with Allure files | site lives only under `grpc-lab/` |

## 9. Done when

1. Lesson 05 approved by the author after the first iteration.
2. All nine lessons on the site with six tabs, RU and EN.
3. `scripts/ci_local.sh` ends with "CI OK" including simulator, scenario-vs-service, E2E and
   translation tests.
4. After merge and push, `https://tomullya.github.io/card-wallet/grpc-lab/` opens and the README
   links to it.
