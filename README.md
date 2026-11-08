# Mini Card Wallet

A demo fintech application built as a QA portfolio project: clients open multi-currency
accounts, issue virtual cards and pay with them. Every card payment is checked by a
separate anti-fraud service over gRPC.

The project shows the full QA cycle on a system I can fully control: business requirements →
design → implementation → automated tests at several levels.

> All data is fictional. Card numbers use the fake prefix `400000` and are not real cards.

## Architecture

```
[Client / tests] ──REST──▶ [Wallet API (FastAPI)] ──gRPC──▶ [Fraud Service]
                                    │
                                    ▼
                              [PostgreSQL]
```

| Component | Technology | Port |
|---|---|---|
| Wallet API | Python 3.13, FastAPI, SQLAlchemy, Alembic | 8000 |
| Fraud Service | Python, gRPC (with reflection and health check) | 50051 |
| Database | PostgreSQL 16 | 5433 (host) |

## Documentation

- [Business requirements](docs/requirements/README.md) — every requirement has an ID (`BR-PAY-03`)
- [Technical design](docs/design/2026-11-08-card-wallet-design.md)
- [API guide slides (Russian, open in a browser)](docs/slides/card-wallet-api-guide.html)
- [API guide (Russian)](docs/api-guide.ru.md) — every endpoint: parameters, what is required and why
- Postman environment: `postman/card-wallet-local.postman_environment.json`
- [Backend implementation plan](docs/plans/2026-11-08-plan-1-backend.md)

## Run locally

Requirements: Docker Desktop, Python 3.13.

```bash
docker compose up -d --build
```

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health
- gRPC: `localhost:50051` — e.g. `grpcurl -plaintext localhost:50051 list`
  or open it in Postman (New → gRPC, server reflection is enabled)

Test merchants for the anti-fraud service: `TEST_TIMEOUT` (answers too late → `503`) and
`TEST_ERROR` (gRPC error → `503`).

## Run the tests

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest            # everything (the stack must be running)
```

| Folder | Level | What it checks |
|---|---|---|
| `tests/unit` | Unit | Commission, Luhn, card expiry, money rounding, fraud rules |
| `tests/api` | API (black box) | Every endpoint: positive, negative, boundary values, auth, access to other clients' data, idempotency, parallel payments |
| `tests/integration` | Integration | Wallet ↔ Fraud Service: approve, decline, timeout, error |
| `tests/grpc` | gRPC | Fraud Service called directly; reflection and health |
| `tests/db` | SQL | Data stored correctly; balance equals the sum of transactions |
| `tests/contract` | Contract | Generated requests (schemathesis) vs. the OpenAPI schema |

Each test is tagged with the requirements it covers: `@pytest.mark.req("BR-PAY-03")`.

Lint: `.venv/bin/ruff check .`

## Defects found during development

| Where found | Defect | Fix |
|---|---|---|
| Requirements review | Card daily limit (max 5000) was checked before the anti-fraud rule "amount > 5000", so that rule could never trigger | Max daily limit raised to 10000 (BR-CARD-02) |
| Contract tests | Login with a password longer than 72 bytes crashed with `500` (bcrypt limit) | Returns `401`; registration rejects such passwords with `422` |
| Contract tests | A request body that is not valid UTF-8 returned an undocumented `400` | Returns `422 VALIDATION_ERROR` like any other invalid input |
| Contract tests | A NUL character (`\u0000`) in any text field crashed with `500` (PostgreSQL cannot store it) | All request bodies reject NUL characters with `422` |
| Code review | Statement with `date_to=9999-12-31` or a huge `offset` crashed with `500` | `200` / `422` |
| Code review | Full PAN could be recovered from its unsalted SHA-256 hash (only 10^6 candidates) | PAN hash is now an HMAC with a server-side secret |
| Code review | CVV could be recovered from the idempotency request hash (1000 guesses) | CVV is excluded from that hash |
