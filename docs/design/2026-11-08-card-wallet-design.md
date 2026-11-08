# Mini Card Wallet — Technical Design

**Date:** 2026-11-08
**Status:** Draft for review
**Deadline:** 2026-12-02
**Business requirements:** [../requirements/README.md](../requirements/README.md)

## 1. Goal

A portfolio project for a QA engineer with fintech (card) background. It shows:

- understanding of a backend (REST API, database, business rules);
- understanding of a frontend and end-to-end flows;
- API testing at several levels (unit, API, contract, integration, gRPC, SQL, E2E);
- REST and gRPC, and the integration between two services;
- QA documentation: requirements, test plan, test cases, checklists, bug reports,
  traceability matrix;
- CI with a public test report.

Code and tests are written with an AI assistant. The project owner drives scope,
reviews the result and must be able to explain every part.

## 2. Architecture

```
[React UI] ──REST──▶ [Wallet API (FastAPI)] ──gRPC──▶ [Fraud Service (Python gRPC)]
                              │
                              ▼
                        [PostgreSQL]
```

| Component | Technology | Responsibility |
|---|---|---|
| Wallet API | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, Pydantic | Auth, accounts, cards, payments, statement |
| Fraud Service | Python 3.13, grpcio | Approve or decline a payment (BR-FRD) |
| Database | PostgreSQL 16 | Wallet data |
| Frontend | React, Vite, TypeScript | Client UI |
| Contract | `proto/fraud.proto` | Shared gRPC contract |
| Runtime | Docker Compose | Starts all components with one command (NFR-07) |

The fraud service is stateless and has no database.

## 3. Data model

| Table | Columns |
|---|---|
| `users` | id (UUID), email (unique, lower case), name, password_hash, created_at |
| `accounts` | id, user_id → users, currency, balance NUMERIC(12,2), created_at; unique (user_id, currency) |
| `cards` | id, account_id → accounts, pan_last4, pan_hash, expiry_date, cvv_hash, status (`ACTIVE`/`BLOCKED`), block_reason, failed_cvv_attempts, daily_limit NUMERIC(12,2), created_at |
| `transactions` | id, account_id, card_id (nullable), parent_id (nullable, commission → payment), type, amount NUMERIC(12,2), currency, status, decline_reason, merchant_name, merchant_category, created_at |
| `idempotency_keys` | user_id, key, request_hash, response_code, response_body (JSON), created_at; primary key (user_id, key) |

Notes:
- The full PAN is not stored after issuing; only last 4 digits and a hash.
- `EXPIRED` is not stored. It is calculated from `expiry_date` when a card is read (BR-CARD-05).
- Balance is stored on the account and changed in the same database transaction that
  saves the transactions. BR-STM-04 checks that it matches the transaction history.

## 4. REST API

Base path `/api/v1`. JWT bearer auth (BR-AUTH-03). Errors follow NFR-03.

| Method | Path | Requirements |
|---|---|---|
| POST | `/auth/register` | BR-AUTH-01 |
| POST | `/auth/login` | BR-AUTH-02 |
| GET | `/me` | BR-AUTH-04 |
| POST, GET | `/accounts` | BR-ACC-01, BR-ACC-02 |
| GET | `/accounts/{id}` | BR-ACC-02 |
| POST | `/accounts/{id}/top-up` | BR-ACC-03 |
| POST | `/accounts/{id}/cards` | BR-CARD-01, BR-CARD-02 |
| GET | `/accounts/{id}/cards` | BR-CARD-03 (list) |
| GET | `/cards/{id}` | BR-CARD-03 |
| POST | `/cards/{id}/block` | BR-CARD-04 |
| POST | `/payments` | BR-PAY-01 … BR-PAY-09 |
| GET | `/accounts/{id}/transactions` | BR-STM-01 … BR-STM-03 |
| GET | `/health` | NFR-06 |

Status codes: `200`/`201` success; `201` with `status: DECLINED` for a business decline;
`401` auth; `404` not found or not owned; `409` conflicts; `422` validation;
`503` fraud service unavailable.

## 5. gRPC contract

```proto
syntax = "proto3";
package fraud.v1;

service FraudService {
  rpc CheckPayment(CheckPaymentRequest) returns (CheckPaymentResponse);
}

message CheckPaymentRequest {
  string transaction_id = 1;
  string user_id = 2;
  string card_last4 = 3;
  string amount = 4;          // decimal as string, e.g. "123.45"
  string currency = 5;
  string merchant_name = 6;
  string merchant_category = 7;
}

enum Decision {
  DECISION_UNSPECIFIED = 0;
  APPROVE = 1;
  DECLINE = 2;
}

message CheckPaymentResponse {
  Decision decision = 1;
  string reason = 2;          // HIGH_AMOUNT, BLOCKED_CATEGORY or empty
  int32 risk_score = 3;
}
```

Amount is a string so that no precision is lost (NFR-01).
Server reflection and the standard health service are enabled (BR-FRD-03).

## 6. Payment flow

`POST /payments` (BR-PAY-02):

1. Validate request → `422`.
2. Look up idempotency key for this user:
   same body hash → return the saved response; different hash → `409`.
3. Load card; check ownership → `404`.
4. Start a DB transaction and lock the account row (`SELECT … FOR UPDATE`) and card row.
5. Checks 1–5 from BR-PAY-02 (blocked, expired, CVV, funds, daily limit).
   Wrong CVV increments the counter and blocks the card on the 3rd attempt (BR-CARD-06).
6. Call the fraud service with a 2-second deadline.
   - Timeout or gRPC error → roll back, return `503`, save nothing (BR-PAY-08).
7. Save transactions, update balance, reset CVV counter on approval, save the
   idempotency record, commit.
8. Return `201` with the payment result.

A declined payment (step 5 or 6) is saved as one `DECLINED` transaction, together with
the idempotency record, in the same commit.

The account lock in step 4 makes parallel payments safe (BR-PAY-09). The lock is held
during the fraud call (max 2 s); this is acceptable for a demo and keeps the logic simple.

## 7. Code structure

```
card-wallet/
├── wallet-api/
│   ├── app/
│   │   ├── main.py            # FastAPI app, routers, error handlers
│   │   ├── config.py          # settings from environment
│   │   ├── db.py              # engine, session
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── routers/           # auth, accounts, cards, payments, transactions, health
│   │   ├── services/          # business logic: payments, cards, commission, luhn
│   │   ├── fraud_client.py    # gRPC client
│   │   └── security.py        # JWT, password and CVV hashing
│   ├── migrations/            # Alembic
│   └── Dockerfile
├── fraud-service/
│   ├── fraud/                 # server.py, rules.py
│   └── Dockerfile
├── proto/fraud.proto
├── frontend/                  # React + Vite + TypeScript
├── tests/
│   ├── unit/                  # commission, luhn, masking, fraud rules
│   ├── api/                   # REST tests per area
│   ├── contract/              # schemathesis vs OpenAPI
│   ├── integration/           # wallet ↔ fraud service
│   ├── grpc/                  # direct fraud service tests
│   ├── db/                    # SQL consistency checks
│   └── e2e/                   # Playwright (Python)
├── postman/                   # collection + environment
├── docs/
│   ├── requirements/          # business requirements
│   ├── design/                # this document
│   └── qa/                    # test plan, test cases, checklists, bug reports, traceability
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

Business logic lives in `services/` and does not depend on FastAPI, so it can be
unit-tested directly.

## 8. Frontend

Pages:
- Login / Register;
- Dashboard: accounts with balances, "Open account";
- Account: top-up, cards list, issue card (PAN and CVV shown once in a dialog),
  block card, statement with filters and pagination;
- Merchant checkout: simulated card payment form.

All interactive elements have `data-testid` attributes for stable E2E tests.
The token is kept in memory and `sessionStorage` (demo app).

## 9. Testing

| Level | Tool | Scope |
|---|---|---|
| Unit | pytest | Commission, Luhn, PAN masking, expiry calculation, fraud rules |
| API | pytest + httpx | Every endpoint: positive, negative, boundary; auth; IDOR; idempotency; CVV blocking; parallel payments |
| Contract | schemathesis | Responses match the OpenAPI schema |
| Integration | pytest | Wallet ↔ fraud: approve, decline, timeout, error |
| gRPC | pytest + grpcio | Fraud service directly |
| DB | pytest + SQL | Balance consistency (BR-STM-04), no balance change on decline |
| Postman | Collection + Newman | Main flows with environment variables and test scripts |
| E2E | Playwright (Python) | Register → open account → top up → issue card → pay → see statement; block card; declined payment |

Test data: each test creates its own user through the API, so tests are independent.
Expired cards are prepared by changing `expiry_date` directly in the database.

Every automated test is tagged with the requirement IDs it covers
(`@pytest.mark.req("BR-PAY-03")`). A small script builds the traceability matrix
(requirement → tests) from these tags.

QA documentation in `docs/qa/`: test plan, test cases, checklists, bug reports,
traceability matrix.

## 10. BUGGY_MODE

`BUGGY_MODE=true` turns on planted defects so that bug reports are reproducible and the
tests can be shown to catch them.

| ID | Defect | Violates |
|---|---|---|
| BUG-01 | Minimum commission 0.50 is ignored | BR-PAY-03 |
| BUG-02 | Payment that reaches the daily limit exactly is declined | BR-PAY-04 |
| BUG-03 | CVV counter is not reset after an approved payment | BR-CARD-06 |
| BUG-04 | `GET /cards/{id}` returns another client's card | BR-CARD-03 |

Each defect has a bug report in `docs/qa/bug-reports/`. A CI job runs the tests with
`BUGGY_MODE=true` and passes only if the expected tests fail.

## 11. CI

GitHub Actions on every push and pull request:
1. Lint (ruff) and unit tests.
2. Start the stack with Docker Compose.
3. API, contract, integration, gRPC, DB tests; Newman; Playwright.
4. Generate the Allure report and publish it to GitHub Pages.
5. BUGGY_MODE job (section 10).

## 12. Out of scope

Transfers between clients, currency conversion, admin role, card unblocking,
real emails, refresh tokens, load testing (k6 only if time remains).

## 13. Risks

| Risk | Mitigation |
|---|---|
| Deadline 2026-12-02 | Build in vertical slices; each slice is usable and tested before the next |
| Flaky parallel-payment and E2E tests | Explicit DB locking; Playwright auto-waits; retries only in E2E |
| Owner cannot explain the code | Short explanation after each slice; learning plan at the end |
