# Test Plan — Mini Card Wallet v1

| | |
|---|---|
| Product | Mini Card Wallet: Wallet API (REST), Fraud Service (gRPC), PostgreSQL |
| Version | v1 (branch `feature/backend` + `feature/qa`) |
| Author | QA Engineer (project owner), with AI assistance |
| Requirements | [`docs/requirements/`](../requirements/README.md) — 38 requirements (BR-*, NFR-*) |
| Date | 2026-11-08 |

## 1. Objective

Confirm that the wallet implements every business requirement correctly and safely, with
special attention to money correctness, card security and access control — the areas where
a defect in a real fintech product costs money or trust.

## 2. Scope

**In scope**

| Area | Requirements |
|---|---|
| Registration, login, token access | BR-AUTH-01 … BR-AUTH-05 |
| Accounts and top-ups | BR-ACC-01 … BR-ACC-03 |
| Card issuing, viewing, blocking, CVV attempts | BR-CARD-01 … BR-CARD-06 |
| Card payments: checks, commission, daily limit, idempotency, concurrency | BR-PAY-01 … BR-PAY-09 |
| Statement: filters, pagination, balance consistency | BR-STM-01 … BR-STM-04 |
| Anti-fraud service and its integration | BR-FRD-01 … BR-FRD-03 |
| Non-functional: money precision, UTC time, error format, sensitive data, docs, health, one-command start, CI | NFR-01 … NFR-08 |

**Out of scope (v1)**

- Transfers between clients, currency conversion, admin role, card unblocking, e-mail.
- Load and performance testing (k6 is a stretch goal).
- Real payment networks and real card data — all data is fictional.

## 3. Test approach

| Level | Tool | What it proves | Location |
|---|---|---|---|
| Unit | pytest | Pure business rules: commission, Luhn, expiry, money rounding, fraud rules | `tests/unit` |
| API (black box) | pytest + httpx | Every endpoint: positive, negative, boundary values, authorization, IDOR | `tests/api` |
| Integration | pytest | Wallet ↔ Fraud Service over gRPC: approve, decline, timeout, error | `tests/integration` |
| gRPC | pytest + grpcio | Fraud Service contract, reflection, health | `tests/grpc` |
| Database | pytest + SQL | Stored data, no plaintext secrets, balance = sum of transactions | `tests/db` |
| Contract | schemathesis | Generated requests never cause 5xx; responses match OpenAPI | `tests/contract` |
| End-to-end (UI) | Playwright (Chromium) | Real user journeys in the web app: registration to statement, errors, session expiry, double click | `tests/e2e` |
| Manual / exploratory | Postman | Main flows, exploratory checks, demo | `postman/` |
| Regression (collection) | Newman | The Postman collection's assertions, in CI | `postman/` |
| Defect detection check | `scripts/verify_bugs_caught.py` | The suite catches each planted defect | `docs/qa/bug-reports` |

Test design techniques used: equivalence partitioning and boundary values (amounts, limits,
lengths), decision tables (payment check order), state transitions (card ACTIVE → BLOCKED,
CVV counter), error guessing (NUL characters, invalid UTF-8, huge numbers), concurrency
(parallel payments, same idempotency key in parallel).

Each automated test is tagged with the requirement IDs it covers; the
[traceability matrix](traceability-matrix.md) is generated from these tags.

## 4. Environments

| Environment | How | Purpose |
|---|---|---|
| Local stack | `docker compose up -d --build` | Web app :3000, Wallet :8000, Fraud :50051, PostgreSQL :5433 |
| Buggy stack | `docker compose --profile buggy up -d` | Same image with planted defects, Wallet :8001 |
| CI | GitHub Actions (`.github/workflows/ci.yml`) | Full run on every push; Allure report |

Test data: every test creates its own client through the API (unique e-mail), so tests are
independent and can run in any order. Expired cards are prepared directly in the database.

## 5. Entry and exit criteria

**Entry:** the stack starts and `GET /api/v1/health` reports `"status": "ok"`.

**Exit (release-ready):**
- 100 % of automated tests pass; contract tests find no 5xx.
- Traceability: every requirement covered by at least one test (`scripts/traceability.py` exits 0).
- Every planted defect is caught (`scripts/verify_bugs_caught.py` exits 0).
- No open defects of severity Critical or Major.

## 6. Risks and mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Double charge on retry or parallel requests | Client loses money | Idempotency tests, parallel payment tests (BR-PAY-07, BR-PAY-09) |
| Rounding errors in commission | Wrong amounts charged | Decimal-only money, boundary tests on commission (BR-PAY-03, NFR-01) |
| Access to another client's data (IDOR) | Data leak | 404 tests for every object type with a second client |
| Card data recoverable from the database | Security incident | DB tests: no full PAN/CVV, keyed hashes (NFR-04) |
| Fraud service down | Payments stuck or charged unchecked | Timeout/error tests: 503, nothing saved (BR-PAY-08) |
| Flaky concurrency tests | False alarms in CI | Database row locks; concurrency tests were run 5 times in a row (`--count=5`) during development |

## 7. Defect management

Defects are recorded in [`bug-reports/`](bug-reports/README.md) using one template:
severity, priority, status, requirement, steps, expected, actual, evidence.
Every fixed defect gets a regression test that failed before the fix.

| Severity | Meaning |
|---|---|
| Critical | Money or card data at risk, or the service crashes on valid input |
| Major | A business rule is broken; no workaround |
| Minor | Wrong behaviour on unusual input, or a workaround exists |
| Trivial | Cosmetic, documentation |

## 8. Deliverables

- This test plan
- [Test cases](test-cases/) by area
- [Checklists](checklists/): smoke, payments regression, security
- [Bug reports](bug-reports/README.md)
- [Traceability matrix](traceability-matrix.md)
- Automated suite (`tests/`), Postman collection (`postman/`), Allure report from CI
