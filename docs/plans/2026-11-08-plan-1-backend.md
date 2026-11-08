# Plan 1 — Backend (Wallet API + Fraud Service) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A running backend — Wallet REST API, gRPC fraud service and PostgreSQL started by `docker compose up` — that implements every business requirement in `docs/requirements/`, covered by unit, API, gRPC, integration, DB and contract tests.

**Architecture:** FastAPI app (`wallet-api/`) with business logic in framework-free `services/`, SQLAlchemy 2 (sync) on PostgreSQL, Alembic migrations. A stateless Python gRPC server (`fraud-service/`) is called by the wallet before charging. Black-box tests in `tests/` run on the host against the compose stack; unit tests import pure functions directly.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2 + psycopg 3, Alembic, PyJWT, bcrypt, grpcio / grpcio-tools / grpcio-reflection / grpcio-health-checking, pytest, httpx, schemathesis, ruff, Docker Compose, PostgreSQL 16.

**Spec:** `docs/design/2026-11-08-card-wallet-design.md` and `docs/requirements/*.md` (requirement IDs are referenced below).

**Later plans:** Plan 2 — frontend + Playwright E2E. Plan 3 — QA docs, Postman/Newman, BUGGY_MODE, CI + Allure, README.

## Global Constraints

- Base path `/api/v1`; Swagger at `/docs` (NFR-05).
- Every error body: `{"error": {"code": str, "message": str}}`, validation adds `"details": [{"field": str, "problem": str}]` (NFR-03).
- Money: `Decimal`, 2 places, `ROUND_HALF_UP`, DB type `NUMERIC(12,2)`; **money is serialized in JSON as a string**, e.g. `"100.00"`; requests accept string or number (NFR-01).
- Timestamps UTC, ISO 8601 with `Z` (NFR-02).
- Not found **or** not owned → `404 NOT_FOUND`, identical body.
- Never log or return full PAN after issuing, CVV after issuing, or passwords (NFR-04). PAN prefix `400000`.
- Ports: wallet `8000`, fraud `50051`, Postgres host port `5433` (container 5432).
- Test env vars (with defaults): `WALLET_URL=http://localhost:8000`, `DB_URL=postgresql://wallet:wallet@localhost:5433/wallet`, `FRAUD_ADDR=localhost:50051`.
- Every test carries `@pytest.mark.req("<ID>", ...)` with the requirement IDs it covers.
- Each test creates its own user (unique email via `uuid4`) — tests never depend on each other.
- Dev loop for API/integration tests: `docker compose up -d --build` then `pytest tests/<dir>`.

## Review Focus

1. Amount sent as a JSON float (`10.1`) must be stored as exactly `10.10`; absurd amounts (`1e30`, `"abc"`) → `422`, never `500`. → Task 4.
2. Login email with surrounding spaces / different case must work. → Task 3.
3. The same `Idempotency-Key` used by two different clients must be independent. → Task 10.
4. A card that is both blocked and expired → `CARD_BLOCKED` (check order). → Task 9.
5. Approved payments from the previous UTC day must not count against today's daily limit. → Task 9.

---

### Task 1: Skeleton, compose stack, health and error format

**Files:**
- Create: `wallet-api/requirements.txt`, `wallet-api/Dockerfile`, `wallet-api/app/__init__.py`, `wallet-api/app/main.py`, `wallet-api/app/config.py`, `wallet-api/app/db.py`, `wallet-api/app/errors.py`, `wallet-api/app/routers/__init__.py`, `wallet-api/app/routers/health.py`
- Create: `docker-compose.yml`, `requirements-dev.txt`, `pytest.ini`, `ruff.toml`, `tests/__init__.py`, `tests/conftest.py`
- Test: `tests/api/test_health.py`, `tests/api/test_errors.py`

**Interfaces:**
- Produces:
  - `app.config.Settings` (pydantic-settings, env names upper-case): `database_url: str`, `jwt_secret: str`, `jwt_ttl_minutes: int = 60`, `fraud_address: str = "fraud:50051"`, `fraud_timeout_seconds: float = 2.0`, `buggy_mode: bool = False`; `get_settings() -> Settings` (cached).
  - `app.db.engine`, `app.db.SessionLocal`, `app.db.get_db() -> Iterator[Session]` (FastAPI dependency).
  - `app.errors.ApiError(status_code: int, code: str, message: str)` exception; `register_error_handlers(app: FastAPI) -> None` mapping `ApiError`, `RequestValidationError` → `422 VALIDATION_ERROR` with `details`, Starlette 404 → `NOT_FOUND`, 405 → `METHOD_NOT_ALLOWED`, unhandled → `500 INTERNAL_ERROR` (no stack trace in body).
  - `tests/conftest.py` fixtures: `api` (session-scoped `httpx.Client(base_url=WALLET_URL + "/api/v1", timeout=10)`), `db` (function-scoped psycopg connection to `DB_URL`, autocommit).
  - `pytest.ini`: registers marker `req(*ids)`; `testpaths = tests`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/api/test_health.py
@pytest.mark.req("NFR-06")
def test_health_returns_ok(api):
    r = api.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"

# tests/api/test_errors.py
@pytest.mark.req("NFR-03")
def test_unknown_route_uses_error_format(api):
    r = api.get("/no-such-route")
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "NOT_FOUND", "message": ANY_STR}}
```
(`ANY_STR`: assert `isinstance(body["error"]["message"], str)` instead of equality.)

- [ ] **Step 2: Run** `pytest tests/api -v` → FAIL (connection refused).

- [ ] **Step 3: Implement**
  - `docker-compose.yml`: `db` (postgres:16, user/password/db `wallet`, host port 5433, healthcheck `pg_isready`), `wallet` (build `wallet-api/`, port 8000, env `DATABASE_URL=postgresql+psycopg://wallet:wallet@db:5432/wallet`, `JWT_SECRET=dev-secret-change-me`, `FRAUD_ADDRESS=fraud:50051`, `depends_on: db (service_healthy)`).
  - `Dockerfile`: `python:3.13-slim`, install requirements, `CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` (alembic added in Task 2; until then CMD is uvicorn only).
  - `GET /api/v1/health` → `{"status": "ok", "database": "ok"|"error"}` using `SELECT 1`; always HTTP 200.
  - `FastAPI(title="Mini Card Wallet API", docs_url="/docs")`, routers mounted under `/api/v1`.

- [ ] **Step 4: Run** `docker compose up -d --build && pytest tests/api -v` → 2 passed.

- [ ] **Step 5: Commit** `git commit -m "feat: project skeleton with health check and error format"`

---

### Task 2: Database models and initial migration

**Files:**
- Create: `wallet-api/app/models.py`, `wallet-api/alembic.ini`, `wallet-api/migrations/env.py`, `wallet-api/migrations/versions/0001_initial.py`
- Modify: `wallet-api/Dockerfile` (CMD runs `alembic upgrade head` first)
- Test: `tests/db/test_schema.py`

**Interfaces:**
- Produces (`app.models`, SQLAlchemy 2 declarative, UUID primary keys `default=uuid4`, `created_at` timezone-aware UTC default now):
  - `class Currency(StrEnum)`: `EUR, USD, PLN`
  - `class CardStatus(StrEnum)`: `ACTIVE, BLOCKED` (stored); `EXPIRED` is computed only.
  - `class BlockReason(StrEnum)`: `BLOCKED_BY_CLIENT, TOO_MANY_FAILED_ATTEMPTS`
  - `class TxType(StrEnum)`: `TOP_UP, PAYMENT, COMMISSION`; `class TxStatus(StrEnum)`: `APPROVED, DECLINED`
  - `class MerchantCategory(StrEnum)`: `GROCERIES, ELECTRONICS, TRAVEL, RESTAURANTS, GAMBLING, OTHER`
  - `User(id, email unique, name, password_hash, created_at)`
  - `Account(id, user_id FK, currency, balance NUMERIC(12,2) default 0, created_at)`, `UniqueConstraint(user_id, currency)`
  - `Card(id, account_id FK, pan_last4, pan_hash, expiry_date: date, cvv_hash, status, block_reason nullable, failed_cvv_attempts int default 0, daily_limit NUMERIC(12,2), created_at)`
  - `Transaction(id, account_id FK, card_id FK nullable, parent_id FK→transactions nullable, type, amount, currency, status, decline_reason nullable, merchant_name nullable, merchant_category nullable, created_at)`, index on `(account_id, created_at)`
  - `IdempotencyKey(user_id FK, key, request_hash, response_code int, response_body JSONB, created_at)`, primary key `(user_id, key)`
  - Enums stored as `VARCHAR` (`Enum(..., native_enum=False)`).

- [ ] **Step 1: Write the failing test**

```python
# tests/db/test_schema.py
@pytest.mark.req("BR-ACC-01")
def test_tables_exist(db):
    names = {r[0] for r in db.execute(
        "select table_name from information_schema.tables where table_schema='public'")}
    assert {"users", "accounts", "cards", "transactions", "idempotency_keys"} <= names

@pytest.mark.req("NFR-01")
def test_money_columns_are_numeric_12_2(db):
    rows = db.execute("""select table_name, column_name, numeric_precision, numeric_scale
        from information_schema.columns
        where column_name in ('balance','amount','daily_limit')""").fetchall()
    assert rows and all(r[2] == 12 and r[3] == 2 for r in rows)
```

- [ ] **Step 2: Run** `pytest tests/db -v` → FAIL.
- [ ] **Step 3: Implement** models and `0001_initial` migration (hand-written or autogenerated, then reviewed); Alembic reads URL from `Settings.database_url`.
- [ ] **Step 4: Run** `docker compose up -d --build && pytest tests/db -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: database models and initial migration"`

---

### Task 3: Authentication (register, login, me)

**Files:**
- Create: `wallet-api/app/security.py`, `wallet-api/app/deps.py`, `wallet-api/app/schemas/__init__.py`, `wallet-api/app/schemas/auth.py`, `wallet-api/app/routers/auth.py`
- Modify: `wallet-api/app/main.py` (mount router)
- Test: `tests/unit/test_security.py`, `tests/api/test_auth.py`, `tests/helpers.py`

**Interfaces:**
- Produces:
  - `security.hash_secret(value: str) -> str`, `security.verify_secret(value: str, hashed: str) -> bool` (bcrypt; used for passwords and CVV).
  - `security.create_access_token(user_id: UUID) -> str` (HS256, claims `sub`, `exp` = now + `jwt_ttl_minutes`); `security.decode_access_token(token: str) -> UUID` raises `ApiError(401, "UNAUTHORIZED", ...)`.
  - `deps.get_current_user(...) -> User` — reads `Authorization: Bearer`, 401 `UNAUTHORIZED` if missing/invalid/unknown user.
  - Responses: register `201 {id, email, name, created_at}`; login `200 {access_token, token_type: "bearer", expires_in: 3600}`; `GET /me` `200 {id, email, name, created_at}`.
  - `tests/helpers.py`: `register_and_login(api) -> AuthedClient` where `AuthedClient` has `.headers: dict`, `.email: str`, `.user_id: str`; `unique_email() -> str`.

- [ ] **Step 1: Write the failing tests** (`tests/api/test_auth.py`, all marked with their BR-AUTH ID)
  - `test_register_success_returns_201_without_password` — body has no `password`/`password_hash` keys; email returned lower-case for input `"User@Example.COM"`.
  - `test_register_duplicate_email_409` — second register with same email in different case → `409`, code `EMAIL_ALREADY_REGISTERED`.
  - `test_register_validation` — parametrized → `422 VALIDATION_ERROR`: email `"not-an-email"`; name `""`; name `"   "`; name 101 chars; password `"short1"` (7 chars); `"onlyletters"`; `"12345678"`.
  - `test_register_password_boundary_8_chars_ok` — `"abcdefg1"` → 201.
  - `test_login_success_returns_token` — `token_type == "bearer"`, `expires_in == 3600`.
  - `test_login_wrong_password_and_unknown_email_same_401` — both `401 INVALID_CREDENTIALS`, identical `message`.
  - `test_login_email_case_and_spaces_ignored` — login with `"  " + email.upper() + " "` → 200. *(Review Focus 2)*
  - `test_me_returns_current_user`.
  - `test_protected_endpoint_rejects_bad_tokens` — parametrized headers: none; `"Bearer garbage"`; `"Token <valid>"`; token signed with other secret; expired token (crafted with PyJWT, `exp` in the past) → all `401 UNAUTHORIZED`.
  - `tests/unit/test_security.py`: `test_hash_secret_is_not_plaintext_and_verifies`, `test_decode_rejects_tampered_token`.
- [ ] **Step 2: Run** `pytest tests/unit/test_security.py tests/api/test_auth.py -v` → FAIL.
- [ ] **Step 3: Implement** schemas (`EmailStr`, name stripped then 1–100, password regex `^(?=.*[A-Za-z])(?=.*\d).{8,}$`), router, `get_current_user`. Normalize email with `.strip().lower()` on register and login.
- [ ] **Step 4: Run** same command after `docker compose up -d --build` → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: registration, login and JWT auth"`

---

### Task 4: Money helpers, accounts and top-up

**Files:**
- Create: `wallet-api/app/services/__init__.py`, `wallet-api/app/services/money.py`, `wallet-api/app/schemas/common.py`, `wallet-api/app/schemas/accounts.py`, `wallet-api/app/schemas/transactions.py`, `wallet-api/app/routers/accounts.py`, `wallet-api/app/services/ownership.py`
- Test: `tests/unit/test_money.py`, `tests/api/test_accounts.py`, `tests/api/test_topup.py`

**Interfaces:**
- Produces:
  - `money.to_money(value: Decimal | str | int) -> Decimal` — quantize `0.01`, `ROUND_HALF_UP`.
  - `money.calculate_commission(amount: Decimal) -> Decimal` — `max(to_money(amount * Decimal("0.01")), Decimal("0.50"))`.
  - `schemas.common.Amount` — `Annotated[Decimal, Field(gt=0, le=Decimal("10000.00"), max_digits=12, decimal_places=2)]`, serialized as string.
  - `schemas.transactions.TransactionOut {id, type, amount, currency, status, decline_reason, merchant_name, card_last4, created_at}`.
  - `ownership.get_owned_account(db, user, account_id: UUID) -> Account` — raises `ApiError(404, "NOT_FOUND", "Account not found")`.
  - Endpoints: `POST /accounts {currency}` → `201 AccountOut {id, currency, balance, created_at}`; `GET /accounts` → `200 [AccountOut]`; `GET /accounts/{id}`; `POST /accounts/{id}/top-up {amount}` → `201 {transaction: TransactionOut, balance}`.
  - `tests/helpers.py` additions: `create_account(api, client, currency="EUR") -> dict`, `top_up(api, client, account_id, amount: str) -> dict`.

- [ ] **Step 1: Write the failing tests**
  - `tests/unit/test_money.py`: `test_calculate_commission` parametrized with the BR-PAY-03 table: `10.00→0.50`, `50.00→0.50`, `100.00→1.00`, `123.45→1.23`, `0.01→0.50`, plus `150.50→1.51` (half-up: 1.505→1.51); `test_to_money_rounds_half_up` (`"0.005"→0.01`).
  - `tests/api/test_accounts.py`: `test_open_account_starts_at_zero` (`balance == "0.00"`); `test_unsupported_currency_422` (`"GBP"`, `"eur"`); `test_second_account_same_currency_409` (`ACCOUNT_ALREADY_EXISTS`); `test_list_returns_only_own_accounts`; `test_other_users_account_404` and `test_random_uuid_404` return identical bodies; `test_non_uuid_id_returns_422_or_404` → 422.
  - `tests/api/test_topup.py`: `test_topup_increases_balance` (`"100.00"` → balance `"100.00"`, transaction `TOP_UP`/`APPROVED`); boundaries parametrized: `"0.01"` → 201, `"10000.00"` → 201, `"0"`/`"-1"`/`"10000.01"`/`"10.555"` → 422; `test_topup_float_is_exact` (JSON number `10.1` → `"10.10"`) *(Review Focus 1)*; `test_topup_absurd_values_422` (`1e30`, `"abc"`, `null`, `true`) *(Review Focus 1)*; `test_topup_other_users_account_404`; `tests/db`: `test_topup_saves_transaction_row` (query `transactions` by account id).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.** Unique-constraint violation → catch `IntegrityError` → 409. Reject bool for amount (Pydantic `strict` or validator).
- [ ] **Step 4: Run** `pytest tests/unit tests/api tests/db -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: accounts, top-up and money helpers"`

---

### Task 5: Card number helpers (pure functions)

**Files:**
- Create: `wallet-api/app/services/card_numbers.py`
- Test: `tests/unit/test_card_numbers.py`

**Interfaces:**
- Produces:
  - `luhn_is_valid(pan: str) -> bool`
  - `generate_pan(prefix: str = "400000") -> str` — 16 digits, last digit = Luhn check digit, uses `secrets`.
  - `mask_pan(last4: str) -> str` → `"**** **** **** 1234"`
  - `expiry_for(issued: date) -> date` — last day of the same month, 3 years later (handle Feb 29 → Feb 28/29 via `calendar.monthrange`).
  - `format_expiry(d: date) -> str` → `"MM/YY"`
  - `is_expired(expiry: date, today: date) -> bool` — `today > expiry`.
  - `generate_cvv() -> str` — 3 digits, may start with 0.
  - `pan_hash(pan: str) -> str` — SHA-256 hex.

- [ ] **Step 1: Write the failing tests**
  - `test_luhn_known_values` (`"4000000000000002"` valid, `"4000000000000001"` invalid, `"79927398713"` valid).
  - `test_generate_pan_format` (1000 iterations: length 16, digits only, prefix `400000`, Luhn valid).
  - `test_mask_pan` → `"**** **** **** 1234"`.
  - `test_expiry_for` parametrized: `2026-11-08 → 2029-11-30`; `2027-02-15 → 2030-02-28`; `2025-02-28 → 2028-02-29`; `2026-01-31 → 2029-01-31`.
  - `test_format_expiry` (`2029-11-30 → "11/29"`).
  - `test_is_expired` (expiry day itself → False; next day → True).
  - `test_generate_cvv_format` (1000 iterations: `re.fullmatch(r"\d{3}", cvv)`).
- [ ] **Step 2: Run** `pytest tests/unit/test_card_numbers.py -v` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: card number, expiry and CVV helpers"`

---

### Task 6: Cards API (issue, list, view, block, expired)

**Files:**
- Create: `wallet-api/app/schemas/cards.py`, `wallet-api/app/services/cards.py`, `wallet-api/app/routers/cards.py`
- Modify: `wallet-api/app/services/ownership.py` (add `get_owned_card`)
- Test: `tests/api/test_cards.py`, `tests/db/test_cards_storage.py`

**Interfaces:**
- Consumes: Task 5 helpers, `ownership.get_owned_account`.
- Produces:
  - `ownership.get_owned_card(db, user, card_id: UUID, *, for_update: bool = False) -> Card` → 404 `NOT_FOUND` "Card not found".
  - `cards.effective_status(card: Card, today: date) -> str` — `BLOCKED` if stored blocked, else `EXPIRED` if `is_expired`, else `ACTIVE`.
  - `cards.issue_card(db, account: Account, daily_limit: Decimal | None) -> tuple[Card, str, str]` (card, full PAN, CVV); active-card count uses `effective_status == ACTIVE`; 4th → `409 CARD_LIMIT_REACHED`.
  - Endpoints: `POST /accounts/{id}/cards {daily_limit?}` → `201 IssuedCardOut {id, account_id, pan, cvv, expiry, status, daily_limit}`; `GET /accounts/{id}/cards` → `[CardOut]`; `GET /cards/{id}` → `CardOut {id, account_id, masked_pan, expiry, status, block_reason, daily_limit}`; `POST /cards/{id}/block` → `200 CardOut`.
  - `tests/helpers.py`: `issue_card(api, client, account_id, daily_limit: str | None = None) -> dict` (returns issue response incl. `pan`, `cvv`); `set_card_expiry(db, card_id, expiry: date)`.

- [ ] **Step 1: Write the failing tests**
  - `test_issue_card_returns_full_pan_and_cvv_once` — `pan` Luhn-valid with prefix `400000`, `cvv` 3 digits, `status == "ACTIVE"`, `daily_limit == "1000.00"`, `expiry` matches `MM/YY` of `expiry_for(today)`; then `GET /cards/{id}` has `masked_pan == "**** **** **** " + pan[-4:]` and no `pan`/`cvv` keys.
  - `test_daily_limit_boundaries` parametrized: `"1.00"`, `"5000.00"` → 201; `"0.99"`, `"5000.01"`, `"0"` → 422.
  - `test_fourth_active_card_409` — 3 issued OK, 4th → `CARD_LIMIT_REACHED`.
  - `test_blocked_card_frees_slot` — block one of 3, issuing again → 201.
  - `test_expired_card_frees_slot_and_shows_expired` — `set_card_expiry(db, id, today - 1 day)` → `GET` shows `EXPIRED`; issuing a new card → 201.
  - `test_block_card` → `BLOCKED`, `block_reason == "BLOCKED_BY_CLIENT"`; second block → `409 CARD_ALREADY_BLOCKED`.
  - `test_list_cards_masked`.
  - `test_other_users_card_and_account_404` — `GET /cards/{id}`, `POST /cards/{id}/block`, `GET/POST /accounts/{id}/cards` by another user → 404.
  - `tests/db/test_cards_storage.py`: `test_full_pan_and_cvv_not_stored` — no column in the `cards` row equals full PAN or CVV; `cvv_hash` starts with `$2`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: card issuing, viewing and blocking"`

---

### Task 7: Fraud service (gRPC)

**Files:**
- Create: `proto/fraudpb/fraud.proto` (contract exactly as design §5, `package fraud.v1`), `scripts/gen_proto.sh`
- Create (generated, committed): `fraud-service/fraudpb/{__init__.py,fraud_pb2.py,fraud_pb2_grpc.py,fraud_pb2.pyi}`, same under `wallet-api/fraudpb/` and `tests/fraudpb/`
- Create: `fraud-service/requirements.txt`, `fraud-service/Dockerfile`, `fraud-service/fraud_service/__init__.py`, `fraud-service/fraud_service/rules.py`, `fraud-service/fraud_service/server.py`
- Modify: `docker-compose.yml` (service `fraud`, port 50051), `docs/design/2026-11-08-card-wallet-design.md` §7 (package name `fraud_service`, proto path)
- Test: `tests/unit/test_fraud_rules.py`, `tests/grpc/test_fraud_service.py`

**Interfaces:**
- Produces:
  - `rules.evaluate(amount: Decimal, merchant_category: str) -> tuple[str, str, int]` → `("DECLINE","HIGH_AMOUNT",90)` if amount > 5000.00; `("DECLINE","BLOCKED_CATEGORY",80)` if category `GAMBLING`; else `("APPROVE","",10)`.
  - `server.serve(port: int = 50051) -> None`; servicer handles `merchant_name == "TEST_TIMEOUT"` → `time.sleep(5)` then normal decision; `"TEST_ERROR"` → `context.abort(grpc.StatusCode.INTERNAL, "simulated error")`; invalid amount string → `INVALID_ARGUMENT`. Reflection + `grpc.health.v1` (status `SERVING`) enabled. Thread pool ≥ 10 workers.
  - `scripts/gen_proto.sh` — runs `python -m grpc_tools.protoc -I proto --python_out=<dir> --grpc_python_out=<dir> --pyi_out=<dir> proto/fraudpb/fraud.proto` for the three target dirs.
  - `tests/conftest.py`: fixture `fraud_stub` → `FraudServiceStub(grpc.insecure_channel(FRAUD_ADDR))`.

- [ ] **Step 1: Write the failing tests**
  - `tests/unit/test_fraud_rules.py` (import via `sys.path` insert of `fraud-service`): parametrized `5000.00 → APPROVE`, `5000.01 → DECLINE HIGH_AMOUNT 90`, `10.00 + GAMBLING → DECLINE BLOCKED_CATEGORY 80`, `6000.00 + GAMBLING → HIGH_AMOUNT` (rule order), `10.00 + GROCERIES → APPROVE "" 10`.
  - `tests/grpc/test_fraud_service.py`: `test_approve`, `test_decline_high_amount`, `test_test_error_returns_internal` (`RpcError.code() == INTERNAL`), `test_test_timeout_exceeds_2s_deadline` (call with `timeout=2` → `DEADLINE_EXCEEDED`), `test_invalid_amount_invalid_argument` (`"abc"`), `test_health_serving`, `test_reflection_lists_service` (reflection stub returns `fraud.v1.FraudService`).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**; run `scripts/gen_proto.sh`.
- [ ] **Step 4: Run** `docker compose up -d --build && pytest tests/unit/test_fraud_rules.py tests/grpc -v` → PASS. Also manually: `grpcurl -plaintext localhost:50051 list` shows `fraud.v1.FraudService` (if grpcurl installed).
- [ ] **Step 5: Commit** `git commit -m "feat: gRPC fraud service with reflection and health"`

---

### Task 8: Fraud client in the wallet + health

**Files:**
- Create: `wallet-api/app/fraud_client.py`
- Modify: `wallet-api/app/routers/health.py`, `wallet-api/requirements.txt` (grpcio), `wallet-api/Dockerfile` (copy `fraudpb/`)
- Test: `tests/api/test_health.py` (extend)

**Interfaces:**
- Produces:
  - `@dataclass FraudDecision(approved: bool, reason: str | None, risk_score: int)`
  - `class FraudUnavailableError(Exception)`
  - `class FraudClient(address: str, timeout_seconds: float)`: `check_payment(*, transaction_id: UUID, user_id: UUID, card_last4: str, amount: Decimal, currency: str, merchant_name: str, merchant_category: str) -> FraudDecision` (any `grpc.RpcError` → `FraudUnavailableError`); `is_healthy() -> bool` (health check, 1 s timeout).
  - `get_fraud_client() -> FraudClient` — module-level singleton dependency built from `Settings`.
  - Health response becomes `{"status": "ok"|"degraded", "database": ..., "fraud_service": "ok"|"error"}`.
- [ ] **Step 1: Test** — `test_health_reports_fraud_service_ok` (`fraud_service == "ok"`, `status == "ok"`).
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: wallet gRPC client for fraud service"`

---

### Task 9: Payments — checks, commission, CVV attempts, fraud decision

**Files:**
- Create: `wallet-api/app/schemas/payments.py`, `wallet-api/app/services/payments.py`, `wallet-api/app/routers/payments.py`
- Test: `tests/api/test_payments.py`, `tests/api/test_cvv_attempts.py`, `tests/integration/test_fraud_integration.py`, `tests/db/test_payment_storage.py`

**Interfaces:**
- Consumes: `get_owned_card(..., for_update=True)`, `calculate_commission`, `effective_status`, `verify_secret`, `FraudClient`.
- Produces:
  - `PaymentRequest {card_id: UUID, cvv: str (pattern ^\d{3}$), amount: Amount, merchant_name: str (stripped, 1–100), merchant_category: MerchantCategory}`; header `Idempotency-Key` required (validated in Task 10; in this task read it with `Header(..., min_length=8, max_length=64)`).
  - `PaymentOut {transaction_id, status, decline_reason, amount, commission (string or null when declined), currency, created_at}`.
  - `payments.process_payment(db, user: User, req: PaymentRequest, fraud: FraudClient) -> PaymentOut` — implements design §6 steps 3–7: lock account (`with_for_update`) then card; checks in BR-PAY-02 order; daily spent = sum of `PAYMENT` `APPROVED` amounts for the card where `created_at >= today 00:00 UTC`; allow when `spent + amount <= daily_limit`; wrong CVV → `failed_cvv_attempts += 1`, at 3 set `BLOCKED` / `TOO_MANY_FAILED_ATTEMPTS`; approval resets counter to 0; fraud reasons mapped `HIGH_AMOUNT→FRAUD_HIGH_AMOUNT`, `BLOCKED_CATEGORY→FRAUD_BLOCKED_CATEGORY`; `FraudUnavailableError` → rollback, `ApiError(503, "FRAUD_SERVICE_UNAVAILABLE", ...)`. Declines commit the CVV counter change and one `DECLINED` transaction. Endpoint returns `201`.
  - `tests/helpers.py`: `pay(api, client, card: dict, amount: str, *, cvv=None, merchant="Shop", category="GROCERIES", key=None) -> httpx.Response` (default `cvv` = card's real CVV, default `key` = `uuid4().hex`); `funded_card(api, client, balance="1000.00", daily_limit=None) -> dict` (account + top-up + card; returns card dict incl. `account_id`, `pan`, `cvv`).

- [ ] **Step 1: Write the failing tests**
  - `test_payments.py`:
    - `test_approved_payment_charges_amount_plus_commission` — balance 1000.00, pay `100.00` → `APPROVED`, `commission == "1.00"`, balance `"899.00"`.
    - `test_min_commission_applied` — pay `10.00` → commission `"0.50"`, balance decreases `10.50`.
    - `test_insufficient_funds_considers_commission` — balance `100.00`: pay `99.50` → DECLINED `INSUFFICIENT_FUNDS` (needs 100.50); pay `99.00` → APPROVED (commission 0.99, total 99.99 ≤ 100.00).
    - `test_exact_balance_allowed` — balance `10.50`, pay `10.00` → APPROVED, balance `"0.00"`.
    - `test_daily_limit_exact_allowed` — limit `100.00`: pay `60.00` then `40.00` → both APPROVED; then `0.01` → `DAILY_LIMIT_EXCEEDED`.
    - `test_declined_payments_do_not_count_to_limit`.
    - `test_yesterdays_payments_do_not_count` — limit `100.00`, pay `100.00`, `UPDATE transactions SET created_at = created_at - interval '1 day'` for that card, pay `100.00` → APPROVED. *(Review Focus 5)*
    - `test_blocked_card_declined` / `test_expired_card_declined` / `test_blocked_and_expired_card_reports_blocked` *(Review Focus 4)*.
    - `test_declined_payment_does_not_change_balance`.
    - `test_payment_validation_422` parametrized: cvv `"12"`, `"1234"`, `"abc"`; amount `"0"`, `"10000.01"`; merchant `""`; category `"CASINO"`; missing `Idempotency-Key`; key 7 chars; key 65 chars.
    - `test_other_users_card_404`.
  - `test_cvv_attempts.py`:
    - `test_three_wrong_cvv_blocks_card` — 3× wrong CVV → each `INVALID_CVV`; card `BLOCKED`/`TOO_MANY_FAILED_ATTEMPTS`; 4th attempt with correct CVV → `CARD_BLOCKED`.
    - `test_success_resets_counter` — wrong, wrong, correct (APPROVED), wrong, wrong → card still `ACTIVE`.
    - `test_other_declines_do_not_count` — wrong, wrong, `INSUFFICIENT_FUNDS` with correct CVV, wrong → card `BLOCKED` only after that 3rd wrong one (i.e., `ACTIVE` before it).
  - `test_fraud_integration.py`: `test_high_amount_declined_by_fraud` (balance 10000.00, limit 5000.00 — card daily limit max is 5000.00 so `5000.01` hits `DAILY_LIMIT_EXCEEDED` first; therefore assert `5000.00` is APPROVED and test `FRAUD_HIGH_AMOUNT` via the gRPC test layer only — document this in the test docstring), `test_gambling_declined` (`FRAUD_BLOCKED_CATEGORY`, balance unchanged), `test_timeout_returns_503_and_saves_nothing` (merchant `TEST_TIMEOUT` → 503 `FRAUD_SERVICE_UNAVAILABLE` within < 4 s, no new transactions, balance unchanged), `test_error_returns_503`.
  - `tests/db/test_payment_storage.py`: `test_approved_creates_payment_and_linked_commission` (2 rows; commission `parent_id` = payment id); `test_declined_creates_single_declined_row`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** `pytest tests/api tests/integration tests/db -v` → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: card payments with limits, commission, CVV blocking and fraud check"`

> Note for the reviewer: because the card daily limit is capped at 5000.00 (BR-CARD-02) and the limit check runs before the fraud check (BR-PAY-02), `FRAUD_HIGH_AMOUNT` is unreachable through the wallet API. This is a real requirements finding — record it in Plan 3 as a bug report / requirements question rather than changing the rules silently.

---

### Task 10: Idempotency and parallel payments

**Files:**
- Create: `wallet-api/app/services/idempotency.py`
- Modify: `wallet-api/app/routers/payments.py`, `wallet-api/app/services/payments.py`
- Test: `tests/api/test_idempotency.py`, `tests/api/test_concurrency.py`

**Interfaces:**
- Produces:
  - `idempotency.request_hash(body: dict) -> str` — SHA-256 of `json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)` over the validated model dumped in JSON mode.
  - `idempotency.find(db, user_id, key) -> IdempotencyKey | None`; `idempotency.save(db, user_id, key, request_hash, code: int, body: dict) -> None` (same DB transaction as the payment).
  - Router flow: existing key + same hash → return stored `(code, body)`; different hash → `409 IDEMPOTENCY_KEY_REUSED`; on `503` nothing saved. Two concurrent first-time requests with the same key: the loser hits the primary-key `IntegrityError` → re-read and return the stored response.
- [ ] **Step 1: Write the failing tests**
  - `test_same_key_same_body_returns_same_response_no_double_charge` — two identical calls → identical JSON; balance charged once; one `PAYMENT` row.
  - `test_same_key_different_body_409`.
  - `test_declined_response_is_replayed` — same key replays the DECLINED result even after the balance is topped up.
  - `test_same_key_different_users_independent` *(Review Focus 3)*.
  - `test_key_reusable_after_503` — `TEST_TIMEOUT` → 503; same key with merchant `"Shop"` → 201 (body differs, but nothing was stored).
  - `test_concurrency.py::test_parallel_payments_never_overdraw` — balance `100.00`, 2 threads pay `60.00` with different keys (use `threading.Barrier`) → exactly one `APPROVED`, one `INSUFFICIENT_FUNDS`, final balance `"39.40"`.
  - `test_concurrency.py::test_parallel_same_key_charges_once` — 5 threads, same key and body → all 201 with the same `transaction_id`; one `PAYMENT` row.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS (run the concurrency file 5× to check for flakiness: `pytest tests/api/test_concurrency.py --count=5` with `pytest-repeat` in `requirements-dev.txt`).
- [ ] **Step 5: Commit** `git commit -m "feat: idempotent payments and race-safe charging"`

---

### Task 11: Statement endpoint and balance consistency

**Files:**
- Create: `wallet-api/app/routers/transactions.py`, `wallet-api/app/services/statement.py`
- Test: `tests/api/test_statement.py`, `tests/db/test_balance_consistency.py`

**Interfaces:**
- Produces:
  - `GET /accounts/{id}/transactions?date_from&date_to&status&type&limit=20&offset=0` → `200 {items: [TransactionOut], total, limit, offset}`, ordered `created_at DESC, id DESC`; `date_to` inclusive (`< date_to + 1 day`).
  - `statement.list_transactions(db, account: Account, filters: StatementFilters) -> tuple[list[Transaction], int]`.
- [ ] **Step 1: Write the failing tests**
  - `test_newest_first_and_fields` — after top-up + payment, items `[COMMISSION, PAYMENT, TOP_UP]` or `[PAYMENT, COMMISSION, TOP_UP]` (same timestamp — assert set of first two and that TOP_UP is last); payment item has `card_last4` and `merchant_name`.
  - `test_filter_by_status_and_type`.
  - `test_date_filters_inclusive` — move one transaction to `2026-01-15 12:00Z` via SQL; `date_from=2026-01-15&date_to=2026-01-15` returns exactly it.
  - `test_date_from_after_date_to_422`; `test_unknown_status_422`.
  - `test_pagination` — 25 top-ups: default page has 20 items, `total == 25`; `offset=20` → 5 items; `limit` `0`/`101`/`offset=-1` → 422.
  - `test_other_users_statement_404`.
  - `tests/db/test_balance_consistency.py::test_balance_equals_sum_of_approved_transactions` — run a mixed scenario (top-ups, approved, declined, CVV failures), then SQL: `balance == SUM(TOP_UP) − SUM(PAYMENT) − SUM(COMMISSION)` over `APPROVED` rows (BR-STM-04).
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `git commit -m "feat: account statement with filters and pagination"`

---

### Task 12: Contract tests, logging check and backend README

**Files:**
- Create: `tests/contract/test_openapi.py`, `tests/api/test_no_sensitive_logs.py`, `README.md` (backend section only — Plan 3 completes it)
- Modify: `wallet-api/app/main.py` (request logging middleware: method, path, status, duration — no bodies)

**Interfaces:**
- Consumes: the whole API.
- [ ] **Step 1: Write the failing tests**
  - `test_openapi.py` — schemathesis loads `WALLET_URL/openapi.json`; for auth-free endpoints and for authenticated endpoints (header hook adding a fresh token), check `not_a_server_error` and `response_schema_conformance`. Max examples 50 per endpoint.
  - `test_no_sensitive_logs.py` — issue a card and make payments (correct and wrong CVV), then `docker compose logs wallet` (via `subprocess`) contains neither the full PAN nor the CVV nor the password (NFR-04). Skip if `docker` is unavailable.
- [ ] **Step 2: Run** → contract test likely FAILS on undeclared responses; fix by declaring `responses={...}` with the error schema on each route.
- [ ] **Step 3: Implement** fixes + logging middleware; README: what the backend is, `docker compose up -d --build`, URLs (`/docs`, gRPC port), how to run each test group.
- [ ] **Step 4: Run** full suite `ruff check . && pytest -v` → all green.
- [ ] **Step 5: Commit** `git commit -m "test: OpenAPI contract tests and sensitive-data log check"`

---

## Requirement coverage (Plan 1)

| Requirement | Task(s) |
|---|---|
| BR-AUTH-01…05 | 3 |
| BR-ACC-01…03 | 4 |
| BR-CARD-01…05 | 5, 6 |
| BR-CARD-06 | 9 |
| BR-PAY-01…06 | 9 |
| BR-PAY-07, BR-PAY-09 | 10 |
| BR-PAY-08 | 9, 10 |
| BR-STM-01…04 | 11 |
| BR-FRD-01…03 | 7, 8, 9 |
| NFR-01…03 | 1, 2, 4 |
| NFR-04 | 6, 12 |
| NFR-05, NFR-06 | 1, 8, 12 |
| NFR-07 | 1, 7 (backend part; frontend in Plan 2) |
| NFR-08 | Plan 3 |
