# Test cases — Accounts and top-ups (BR-ACC)

### TC-ACC-001 Open an account

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-01 | High | Positive | `tests/api/test_accounts.py::test_open_account_starts_at_zero` |

**Steps:** `POST /accounts` with `{"currency": "USD"}`.
**Expected result:** 201; `currency` = USD; `balance` = `"0.00"` (a string).

### TC-ACC-002 One account per currency

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-01 | High | Negative | `tests/api/test_accounts.py::test_second_account_same_currency_409`, `tests/db/test_schema.py::test_one_account_per_currency_constraint` |

**Steps:** open EUR twice.
**Expected result:** second → 409 `ACCOUNT_ALREADY_EXISTS`; the database has a unique constraint on (user_id, currency).

### TC-ACC-003 Unsupported currency

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-01 | Medium | Negative | `tests/api/test_accounts.py::test_unsupported_currency_422` |

**Steps:** open with `GBP`, `eur`, `""`, `null`.
**Expected result:** each → 422.

### TC-ACC-004 Another client's account is invisible

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-02 | High | Security | `tests/api/test_accounts.py::test_other_users_account_and_random_id_same_404`, `tests/api/test_accounts.py::test_list_returns_only_own_accounts` |

**Steps:** 1. Client B requests client A's account id. 2. Client B requests a random UUID. 3. Client B lists accounts.
**Expected result:** steps 1 and 2 → identical 404 bodies; step 3 shows only B's accounts.

### TC-ACC-005 Top-up amount boundaries

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-03 | High | Boundary | `tests/api/test_topup.py::test_topup_boundaries_accepted`, `tests/api/test_topup.py::test_topup_invalid_amount_422` |

**Steps:** top up with each value.
**Expected result:** `0.01`, `10000.00` → 201. `0`, `0.00`, `-1`, `10000.01`, `10.555` → 422.

### TC-ACC-006 Top-up money precision

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-03, NFR-01 | High | Positive | `tests/api/test_topup.py::test_topup_float_is_exact`, `tests/api/test_topup.py::test_topups_accumulate` |

**Steps:** 1. Top up with the JSON number `10.1`. 2. On a new account top up `0.10` then `0.20`.
**Expected result:** step 1 balance `"10.10"`; step 2 balance `"0.30"` (no floating-point error).

### TC-ACC-007 Absurd top-up values

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-03 | Medium | Negative | `tests/api/test_topup.py::test_topup_absurd_values_422` |

**Steps:** top up with `1e30`, `"abc"`, `null`, `true`, `"NaN"`, `"Infinity"`, `[]`, `{}`.
**Expected result:** each → 422, never 500.

### TC-ACC-008 Top-up is stored correctly

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-ACC-03 | Medium | Positive | `tests/db/test_topup_storage.py::test_topup_saves_transaction_row` |

**Steps:** top up `25.50` on a PLN account; query `transactions` and `accounts`.
**Expected result:** one row `TOP_UP / APPROVED / 25.50 / PLN`; account balance 25.50.
