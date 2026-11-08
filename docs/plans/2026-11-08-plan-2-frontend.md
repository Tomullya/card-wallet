# Plan 2 — Frontend + E2E Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A small React web client for the wallet (login, accounts, top-up, cards, checkout, statement) served by docker compose, covered by Playwright end-to-end tests that run in the same pytest suite and CI.

**Architecture:** `frontend/` is a Vite + React + TypeScript single-page app. In docker compose an nginx container serves the built files on port 3000 and proxies `/api/` to the wallet, so the browser talks to one origin (no CORS). In development `vite` proxies `/api` to `localhost:8000`. One typed API client wraps `fetch`, adds the bearer token, and turns the wallet's error format into an `ApiError`. E2E tests are Python Playwright tests in `tests/e2e/`, tagged with requirement IDs like every other test.

**Tech Stack:** React 18.3, react-router-dom 6, TypeScript 5.6, Vite 5.4, nginx 1.27 (alpine), Python Playwright + pytest-playwright (Chromium).

**Spec:** `docs/design/2026-11-08-card-wallet-design.md` §8 (Frontend), §9 (E2E row); `docs/requirements/` (behaviour the UI exposes); NFR-07 (one-command start includes the frontend).

## Global Constraints

- Every interactive element and every value a test reads has a `data-testid` (kebab-case, e.g. `login-email`, `account-balance`).
- Money is displayed exactly as the API returns it (a string) plus the currency; the UI never does arithmetic on money.
- The token is kept in `sessionStorage` under `cw.token`; a 401 from any call clears it and sends the user to `/login` with the message "Session expired — please log in again".
- Each payment submission generates one `Idempotency-Key` (`crypto.randomUUID()`) and reuses it if the same submission is retried; the Pay button is disabled while a request is pending.
- Error messages show the API's `error.message`; validation errors list `details[].field: problem`.
- Full PAN and CVV are shown only in the "card issued" dialog and are never stored in browser storage.
- UI language: English (matches the API and docs). Fictional data only.
- Frontend URL: `http://localhost:3000`; test env var `FRONTEND_URL` (default that).

## Review Focus

1. Token expires mid-session → the next action redirects to login with a message, not a blank page or endless spinner. → Task 2.
2. Double-click on Pay → exactly one payment is charged. → Task 5.
3. Fraud service unavailable (503) → a clear "try again" message; nothing shown as paid. → Task 5.
4. Opening `/accounts/<another client's id>` → a "not found" view, no crash. → Task 4.
5. Money strings such as `"0.50"` and `"10000.00"` are shown unchanged (no `0.5`, no `10000`). → Task 4.

---

### Task 1: Frontend skeleton, nginx, compose, E2E harness

**Files:**
- Create: `frontend/package.json`, `frontend/package-lock.json` (generated), `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/styles.css`, `frontend/src/api.ts`, `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore`
- Create: `tests/e2e/__init__.py`, `tests/e2e/conftest.py`, `tests/e2e/test_smoke.py`
- Modify: `docker-compose.yml` (service `frontend`, port `3000:80`, depends on `wallet`), `requirements-dev.txt` (`pytest-playwright`)

**Interfaces:**
- Produces:
  - `api.ts`: `class ApiError extends Error { status: number; code: string; details?: {field: string; problem: string}[] }`; `request<T>(method: string, path: string, body?: unknown, headers?: Record<string,string>): Promise<T>` — prefixes `/api/v1`, adds `Authorization` from `getToken()`, parses the error format, on 401 calls the registered `onUnauthorized` handler; `getToken()`, `setToken(t: string | null)`, `setUnauthorizedHandler(fn: () => void)`.
  - Routes (react-router): `/login`, `/register`, `/` (dashboard), `/accounts/:id`, `/pay`, `*` (not found). Task 1 renders placeholders; later tasks fill them.
  - nginx: serves `/usr/share/nginx/html`, `try_files $uri /index.html`, `location /api/ { proxy_pass http://wallet:8000; }`.
  - `tests/e2e/conftest.py`: `FRONTEND_URL`; fixture `app(page)` → `page` with `base_url` set; fixture `signed_in(page, api)` → registers a user via API, logs in through the UI, returns `(page, AuthedClient)`.
- [ ] **Step 1: Failing test** `tests/e2e/test_smoke.py::test_login_page_loads` (`req("NFR-07")`) — `page.goto(FRONTEND_URL + "/login")`; `get_by_test_id("login-email")` visible; page title contains "Card Wallet".
- [ ] **Step 2: Run** `.venv/bin/pytest tests/e2e -q` → FAIL (connection refused).
- [ ] **Step 3: Implement** skeleton, Dockerfile (node:24-alpine build → nginx:1.27-alpine), compose service; `npm install` to create the lockfile.
- [ ] **Step 4: Run** `docker compose up -d --build frontend && .venv/bin/pytest tests/e2e -q` → PASS; `npm --prefix frontend run build` → no TypeScript errors.
- [ ] **Step 5: Commit** `feat(frontend): skeleton served by nginx with E2E harness`

### Task 2: Register, login, logout, session expiry

**Files:** Create `frontend/src/auth.tsx` (context: `user`, `login(email, password)`, `register(email, name, password)`, `logout()`), `frontend/src/pages/Login.tsx`, `frontend/src/pages/Register.tsx`, `frontend/src/components/Layout.tsx` (header with user name and `logout-button`), `frontend/src/components/ErrorBanner.tsx`; Test `tests/e2e/test_auth_ui.py`.

**Interfaces:**
- Test ids: `register-email`, `register-name`, `register-password`, `register-submit`, `login-email`, `login-password`, `login-submit`, `error-banner`, `user-name`, `logout-button`, `session-message`.
- Unauthenticated access to any route except `/login` and `/register` redirects to `/login`.
- [ ] **Step 1: Failing tests** (`req` IDs in brackets):
  - `test_register_then_land_on_dashboard` [BR-AUTH-01] — fill register form → dashboard shows `user-name` = the name.
  - `test_login_wrong_password_shows_error` [BR-AUTH-02] — `error-banner` contains "Invalid email or password".
  - `test_register_validation_error_shown` [BR-AUTH-01] — password `short12` → banner mentions `password`.
  - `test_logout_returns_to_login` [BR-AUTH-03].
  - `test_expired_session_redirects_to_login` [BR-AUTH-03] — signed in, then `page.evaluate("sessionStorage.setItem('cw.token','garbage')")`, reload dashboard → `/login` with `session-message`. *(Review Focus 1)*
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4: Run** → PASS (rebuild frontend container first).
- [ ] **Step 5: Commit** `feat(frontend): registration, login and session handling`

### Task 3: Dashboard — accounts

**Files:** Create `frontend/src/pages/Dashboard.tsx`, `frontend/src/money.ts` (`formatMoney(amount: string, currency: string): string` → `"89.50 EUR"`, no number conversion); Test `tests/e2e/test_accounts_ui.py`.

**Interfaces:** test ids `account-card-<CURRENCY>` (link to `/accounts/:id`), `account-balance-<CURRENCY>`, `open-account-currency` (select EUR/USD/PLN), `open-account-submit`, `empty-accounts`.
- [ ] **Step 1: Failing tests:** `test_empty_state_then_open_account` [BR-ACC-01] — empty state, open EUR → card shows `0.00 EUR`; `test_second_account_same_currency_shows_conflict` [BR-ACC-01] — banner "already have a EUR account".
- [ ] **Steps 2–4** as usual. **Step 5: Commit** `feat(frontend): dashboard with accounts`

### Task 4: Account page — top-up, cards, statement

**Files:** Create `frontend/src/pages/Account.tsx`, `frontend/src/components/TopUpForm.tsx`, `frontend/src/components/Cards.tsx` (list, issue with optional daily limit, block, issued dialog), `frontend/src/components/Statement.tsx` (filters status/type/date_from/date_to, pagination 10 per page, `total`); Test `tests/e2e/test_account_ui.py`.

**Interfaces:** test ids `account-balance`, `topup-amount`, `topup-submit`, `issue-limit`, `issue-submit`, `issued-pan`, `issued-cvv`, `issued-close`, `card-row` (each card; children `card-masked`, `card-status`, `card-block`), `statement-row` (children `tx-type`, `tx-amount`, `tx-status`, `tx-reason`), `statement-total`, `filter-status`, `filter-type`, `statement-next`, `statement-prev`, `not-found`.
- [ ] **Step 1: Failing tests:**
  - `test_top_up_updates_balance` [BR-ACC-03] — top up `10000.00` → `account-balance` = `10000.00 EUR` exactly *(Review Focus 5)*; `0` → banner, balance unchanged.
  - `test_issue_card_shows_pan_once` [BR-CARD-02, BR-CARD-03] — dialog shows 16-digit `400000…` and 3-digit CVV; after closing, `card-masked` = `**** **** **** <last4>` and the full PAN is nowhere in `page.content()`.
  - `test_block_card` [BR-CARD-04] — status becomes BLOCKED.
  - `test_statement_filters_and_pages` [BR-STM-02, BR-STM-03] — 12 top-ups via API → 10 rows, `statement-total` 12, next page 2 rows; filter type COMMISSION → 0 rows.
  - `test_foreign_account_shows_not_found` [BR-ACC-02] — another client's account id → `not-found` visible. *(Review Focus 4)*
- [ ] **Steps 2–4.** **Step 5: Commit** `feat(frontend): account page with top-up, cards and statement`

### Task 5: Checkout — card payment

**Files:** Create `frontend/src/pages/Pay.tsx`; Test `tests/e2e/test_pay_ui.py`.

**Interfaces:** test ids `pay-card` (select of the user's ACTIVE cards, label `masked · currency`), `pay-cvv`, `pay-amount`, `pay-merchant`, `pay-category`, `pay-submit`, `pay-result` (with `pay-status`, `pay-reason`, `pay-commission`). One `Idempotency-Key` per submission (generated when the form is submitted, kept for a retry of the same values, renewed when any field changes).
- [ ] **Step 1: Failing tests:**
  - `test_full_journey` [BR-PAY-05, BR-STM-01] — register in UI → open EUR → top up 100.00 → issue card (read CVV from dialog) → pay 10.00 → `pay-status` APPROVED, `pay-commission` `0.50 EUR` *(Review Focus 5)* → account balance `89.50 EUR` → statement has PAYMENT and COMMISSION rows.
  - `test_wrong_cvv_declined` [BR-CARD-06] — `pay-status` DECLINED, `pay-reason` INVALID_CVV.
  - `test_double_click_pays_once` [BR-PAY-07] — `pay-submit` double-clicked → balance charged once (check via API). *(Review Focus 2)*
  - `test_fraud_unavailable_message` [BR-PAY-08] — merchant `TEST_TIMEOUT` → banner contains "try again"; no `pay-result`; balance unchanged. *(Review Focus 3)*
- [ ] **Steps 2–4.** **Step 5: Commit** `feat(frontend): checkout page`

### Task 6: CI, docs, traceability

**Files:** Modify `scripts/ci_local.sh` (wait for `http://localhost:3000`, `npm --prefix frontend ci && npm --prefix frontend run build` typecheck step), `.github/workflows/ci.yml` (`python -m playwright install --with-deps chromium`; frontend npm cache path), `README.md` (frontend section, screenshot `docs/slides/…` not required), `docs/qa/test-plan.md` (E2E row; frontend in scope), `scripts/traceability.py` (remove the NFR-07 "partly" note), `docs/requirements/NFR.md` untouched.

- [ ] **Step 1:** `scripts/ci_local.sh` → must end with `CI OK` including the E2E tests; `traceability.py` exits 0.
- [ ] **Step 2: Commit** `ci: frontend build and E2E tests in CI; docs updated`
