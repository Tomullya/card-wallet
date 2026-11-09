# Mini Card Wallet — fintech QA portfolio project

A demo card wallet — multi-currency accounts, virtual cards, card payments with commission,
daily limits and anti-fraud checks — built to show the **full QA cycle** on a system I fully
control: requirements → design → implementation → automated tests at six levels →
QA documentation → CI.

I am a QA engineer with a fintech (card) background. The code and tests were written with an
AI assistant; I drove the scope, requirements and review, and the QA design is mine.

> All data is fictional. Card numbers use the fake prefix `400000`.

[![CI](https://github.com/Tomullya/card-wallet/actions/workflows/ci.yml/badge.svg)](https://github.com/Tomullya/card-wallet/actions/workflows/ci.yml)  ·  **Allure report:** https://tomullya.github.io/card-wallet/  ·  **gRPC trainer:** https://tomullya.github.io/card-wallet/grpc-lab/

## What this project demonstrates

| Skill | Where to look |
|---|---|
| Requirements analysis (and finding a requirements defect before coding) | [`docs/requirements/`](docs/requirements/README.md), [BUG-05](docs/qa/bug-reports/BUG-05.md) |
| Test design: boundaries, decision tables, state transitions, concurrency | [Test cases](docs/qa/test-cases/), [checklists](docs/qa/checklists/) |
| REST API testing (positive, negative, boundary, auth, IDOR) | [`tests/api/`](tests/api/) — pytest + httpx |
| gRPC testing: all 4 call types (unary, server / client / bidirectional streaming), metadata auth, request ids, deadlines, every status code | [`tests/grpc/`](tests/grpc/), [`tests/integration/`](tests/integration/) |
| **Interactive gRPC trainer (RU/EN):** comics, a sandbox proven equal to the real service in CI, quizzes | **[tomullya.github.io/card-wallet/grpc-lab](https://tomullya.github.io/card-wallet/grpc-lab/)** · source [`site/grpc-lab/`](site/grpc-lab/) |
| gRPC exercises: 9 lessons with auto-checked tests | [`docs/grpc-lab/`](docs/grpc-lab/README.md), [`grpc-lab/`](grpc-lab/) |
| SQL checks on stored data | [`tests/db/`](tests/db/) |
| Contract testing against OpenAPI | [`tests/contract/`](tests/contract/) — schemathesis |
| UI end-to-end testing | [`tests/e2e/`](tests/e2e/) — Playwright, full user journey in a browser |
| Postman / Newman | [`postman/`](postman/) — 27 requests, 49 assertions |
| Bug reporting | [19 bug reports](docs/qa/bug-reports/README.md) |
| Traceability | [Matrix: every requirement has at least one test](docs/qa/traceability-matrix.md) — generated from test tags (NFR-08 partly: see the matrix note) |
| Proving the tests find bugs | `BUGGY_MODE`: 7 planted defects (4 REST, 3 gRPC), each caught by a named test |
| CI | [GitHub Actions](.github/workflows/ci.yml) + Allure report |

## Architecture

```
[Web app / Postman / tests] ──REST──▶ [Wallet API (FastAPI)] ──gRPC──▶ [Fraud Service]
                                              │
                                              ▼
                                        [PostgreSQL]
```

| Component | Technology | Port |
|---|---|---|
| Web app | React, TypeScript, Vite; served by nginx (proxies `/api`) | 3000 |
| Wallet API | Python 3.13, FastAPI, SQLAlchemy, Alembic | 8000 |
| Fraud Service | Python gRPC: 5 methods incl. 3 streaming, API-key metadata, reflection, health check | 50051 |
| Database | PostgreSQL 16 | 5433 |
| Wallet with planted defects (optional) | same image, `BUGGY_MODE=true` | 8001 |
| Fraud Service with planted defects (optional) | same image, `BUGGY_MODE=true` | 50052 |

Business rules worth testing: commission 1 % (min 0.50), daily card limit, block after
3 wrong CVV, idempotent payments, no overdraft under parallel requests, anti-fraud timeout →
503 with nothing saved. Details: [API guide (RU)](docs/api-guide.ru.md) ·
[slides (RU)](docs/slides/card-wallet-api-guide.html) · [design](docs/design/2026-11-08-card-wallet-design.md).

## Run it

Requirements: Docker, Python 3.13, Node.js (for Newman and Allure), Java (for Allure).

```bash
docker compose up -d --build            # app: http://localhost:3000 · Swagger: http://localhost:8000/docs
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/playwright install chromium
npm ci
scripts/ci_local.sh                     # everything CI runs; ends with "CI OK"
```

Single pieces:

```bash
.venv/bin/pytest                        # all automated tests (the stack must be running)
scripts/run_newman.sh                   # Postman collection
npx allure open reports/allure-report   # view the report after ci_local.sh
```

Postman: import `postman/card-wallet.postman_collection.json` and
`postman/card-wallet-local.postman_environment.json`, run top to bottom.
gRPC in Postman: New → gRPC → `localhost:50051` (methods load via reflection); add metadata
`x-api-key: dev-wallet-key`. Step-by-step lessons: [`docs/grpc-lab/`](docs/grpc-lab/README.md).

## Automated tests — 392 (+34 simulator tests in Node)

| Level | Folder | Tests | What it checks |
|---|---|---|---|
| Unit | `tests/unit` | 67 | Commission, Luhn, expiry, money rounding, fraud rules, API-key roles, event hub, trainer texts RU/EN, QA tooling |
| API | `tests/api` | 138 | Every endpoint: positive, negative, boundaries, auth, other clients' data, idempotency, parallel payments |
| Integration | `tests/integration` | 5 | Wallet ↔ Fraud Service: approve, decline, timeout, error; REST payment appears in the gRPC event stream |
| gRPC | `tests/grpc` | 80 | Fraud Service directly: 4 call types, metadata, deadlines, cancellation, limits, every status code, reflection, health; every trainer-sandbox scenario against the real service |
| Database | `tests/db` | 9 | Stored data, no plaintext card data, balance = sum of transactions |
| Contract | `tests/contract` | 1 (14 endpoints) | Generated requests never cause 5xx; responses and status codes match OpenAPI |
| E2E (browser) | `tests/e2e` | 92 | Wallet: register → account → top-up → card → pay → statement; errors, session expiry, double click. gRPC trainer site: lessons, RU/EN, themes, sandbox presets, quizzes, progress |

Counts include parametrized cases. Every test is tagged with the requirements it covers
(`@pytest.mark.req("BR-PAY-03")`); `scripts/traceability.py` builds the matrix and fails CI
if a requirement has no test.

## BUGGY_MODE — do the tests really catch bugs?

```bash
docker compose --profile buggy up -d
.venv/bin/python scripts/verify_bugs_caught.py
```

```
BUG     normal  buggy            test
BUG-01  pass    fail (caught)    tests/api/test_payments.py::test_min_commission_applied
BUG-02  pass    fail (caught)    tests/api/test_payments.py::test_daily_limit_exact_allowed
BUG-03  pass    fail (caught)    tests/api/test_cvv_attempts.py::test_success_resets_counter
BUG-04  pass    fail (caught)    tests/api/test_cards.py::test_other_users_card_and_account_404
BUG-17  pass    fail (caught)    tests/grpc/test_metadata.py::test_unknown_key_unauthenticated
BUG-18  pass    fail (caught)    tests/grpc/test_bidi_streaming.py::test_stream_ends_after_client_closes
BUG-19  pass    fail (caught)    tests/grpc/test_metadata.py::test_request_id_echoed_in_trailers
All planted defects are caught.
```

## Defects found during development

Seven real defects. The six code defects were fixed with a regression test that failed
before the fix; the requirements defect was fixed in the requirements and is covered by a test
([all bug reports](docs/qa/bug-reports/README.md)):

| How it was found | Defect |
|---|---|
| Requirements review | Daily limit (max 5000) blocked the anti-fraud rule "amount > 5000" from ever triggering — [BUG-05](docs/qa/bug-reports/BUG-05.md) |
| Contract tests | Password over 72 bytes crashed login with 500 — [BUG-06](docs/qa/bug-reports/BUG-06.md) |
| Contract tests | Non-UTF-8 body returned an undocumented 400 — [BUG-07](docs/qa/bug-reports/BUG-07.md) |
| Contract tests | NUL character in any text field crashed with 500 — [BUG-08](docs/qa/bug-reports/BUG-08.md) |
| Code review | Statement with an extreme date or offset crashed with 500 — [BUG-09](docs/qa/bug-reports/BUG-09.md) |
| Code review | Full card number recoverable from an unsalted hash — [BUG-10](docs/qa/bug-reports/BUG-10.md) |
| Code review | CVV recoverable from the idempotency hash — [BUG-11](docs/qa/bug-reports/BUG-11.md) |

## Documentation

- [Business requirements](docs/requirements/README.md) — 44 requirements with IDs and acceptance criteria
- [Technical design](docs/design/2026-11-08-card-wallet-design.md)
- [QA documentation](docs/qa/README.md) — test plan, 50 test cases, checklists, bug reports, traceability matrix
- [API guide (RU)](docs/api-guide.ru.md) and [slides (RU)](docs/slides/card-wallet-api-guide.html)
- Implementation plans: [backend](docs/plans/2026-11-08-plan-1-backend.md), [QA package](docs/plans/2026-11-08-plan-3-qa.md)
