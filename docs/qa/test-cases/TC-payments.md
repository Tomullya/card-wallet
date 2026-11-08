# Test cases — Card payments (BR-PAY)

Default preconditions: client with an EUR account (balance given per case) and an ACTIVE card.

### TC-PAY-001 Approved payment charges amount plus commission

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-03, BR-PAY-05 | Critical | Positive | `tests/api/test_payments.py::test_approved_payment_charges_amount_plus_commission`, `tests/db/test_payment_storage.py::test_approved_creates_payment_and_linked_commission` |

**Steps:** balance 1000.00; pay 100.00.
**Expected result:** 201 APPROVED, `commission` `"1.00"`; balance `"899.00"`; DB has PAYMENT 100.00 and COMMISSION 1.00 whose `parent_id` = the payment.

### TC-PAY-002 Minimum commission

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-03 | High | Boundary | `tests/api/test_payments.py::test_min_commission_applied`, `tests/unit/test_money.py::test_calculate_commission` |

**Steps:** balance 100.00; pay 10.00.
**Expected result:** commission `"0.50"`, balance `"89.50"`. Unit table: 0.01 → 0.50, 123.45 → 1.23, 150.50 → 1.51. (Planted defect BUG-01 breaks this.)

### TC-PAY-003 Balance check includes commission

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-02 | Critical | Boundary | `tests/api/test_payments.py::test_insufficient_funds_considers_commission`, `tests/api/test_payments.py::test_exact_balance_allowed` |

**Steps:** balance 100.00: pay 99.50, then 99.00. Separately: balance 10.50, pay 10.00.
**Expected result:** 99.50 → DECLINED `INSUFFICIENT_FUNDS` (needs 100.50); 99.00 → APPROVED (99.99), balance `"0.01"`; 10.00 on 10.50 → APPROVED, balance `"0.00"`.

### TC-PAY-004 Daily limit: exact amount allowed

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-04 | High | Boundary | `tests/api/test_payments.py::test_daily_limit_exact_allowed`, `tests/api/test_payments.py::test_commission_does_not_count_to_limit` |

**Steps:** card limit 100.00: pay 60.00, 40.00, then 0.01.
**Expected result:** 60.00 and 40.00 APPROVED; 0.01 → `DAILY_LIMIT_EXCEEDED`. Commission is not counted. (Planted defect BUG-02 declines the 40.00.)

### TC-PAY-005 Daily limit counts only today's approved payments

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-04 | Medium | Positive | `tests/api/test_payments.py::test_declined_payments_do_not_count_to_limit`, `tests/api/test_payments.py::test_yesterdays_payments_do_not_count` |

**Steps:** limit 100.00: a declined 100.00 (gambling), then 100.00. Separately: pay 100.00, move it to yesterday in the DB, pay 100.00.
**Expected result:** the second payment is APPROVED in both cases.

### TC-PAY-006 Check order: blocked before expired

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-02 | Medium | Decision table | `tests/api/test_payments.py::test_blocked_and_expired_card_reports_blocked`, `tests/api/test_payments.py::test_blocked_card_declined`, `tests/api/test_payments.py::test_expired_card_declined` |

**Expected result:** blocked → `CARD_BLOCKED`; expired → `CARD_EXPIRED`; both → `CARD_BLOCKED`.

### TC-PAY-007 Declined payment changes nothing

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-06 | High | Negative | `tests/api/test_payments.py::test_declined_payment_does_not_change_balance`, `tests/db/test_payment_storage.py::test_declined_creates_single_declined_row` |

**Steps:** balance 50.00; pay 60.00.
**Expected result:** 201 DECLINED `INSUFFICIENT_FUNDS`, `commission` null; balance `"50.00"`; one DECLINED PAYMENT row with the reason.

### TC-PAY-008 Request validation

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-01 | Medium | Negative | `tests/api/test_payments.py::test_payment_field_validation_422`, `tests/api/test_payments.py::test_idempotency_key_validation_422`, `tests/api/test_payments.py::test_idempotency_key_boundaries_ok` |

**Expected result:** CVV `12` / `1234` / `abc`, amount `0` / `10000.01` / `1.001`, empty or 101-character merchant, category `CASINO`, non-UUID card id, missing key, key of 7 or 65 characters → 422. Keys of 8 and 64 characters → 201.

### TC-PAY-009 Idempotent retry

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-07 | Critical | Positive | `tests/api/test_idempotency.py::test_same_key_same_body_returns_same_response_no_double_charge`, `tests/api/test_idempotency.py::test_same_key_different_body_409`, `tests/api/test_idempotency.py::test_same_key_different_users_independent` |

**Steps:** send the same payment twice with one key; then the same key with another amount; then the same key from another client.
**Expected result:** identical responses, charged once; different amount → 409 `IDEMPOTENCY_KEY_REUSED`; another client's payment is independent.

### TC-PAY-010 Parallel payments never overdraw

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-09 | Critical | Concurrency | `tests/api/test_concurrency.py::test_parallel_payments_never_overdraw`, `tests/api/test_concurrency.py::test_parallel_same_key_charges_once` |

**Steps:** balance 100.00; two threads pay 60.00 at the same moment. Separately: five threads send the same key.
**Expected result:** exactly one APPROVED, one `INSUFFICIENT_FUNDS`, balance `"39.40"`. Same key ×5 → one transaction, one charge.
