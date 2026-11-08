# Test cases — Statement (BR-STM)

### TC-STM-001 Order and fields

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-STM-01 | High | Positive | `tests/api/test_statement.py::test_newest_first_and_fields` |

**Steps:** top up, pay 10.00 at "Cafe", get the statement.
**Expected result:** newest first (TOP_UP last); the payment item has `card_last4` and `merchant_name`; top-up has `card_last4` null.

### TC-STM-002 Filters by status and type

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-STM-02 | Medium | Positive | `tests/api/test_statement.py::test_filter_by_status_and_type` |

**Expected result:** `status=DECLINED` → only the declined payment; `type=COMMISSION` → only commissions; combined filters work; `total` matches.

### TC-STM-003 Date filters are inclusive

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-STM-02 | Medium | Boundary | `tests/api/test_statement.py::test_date_filters_inclusive` |

**Steps:** move a transaction to `2026-01-15T23:59:59Z`; filter `date_from=date_to=2026-01-15`, then `date_to=2026-01-14`, then `date_from=2026-01-16`.
**Expected result:** only that transaction; then 0; then the other one.

### TC-STM-004 Invalid filters

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-STM-02 | Medium | Negative | `tests/api/test_statement.py::test_invalid_filters_422`, `tests/api/test_statement.py::test_max_date_to_is_not_a_server_error` |

**Expected result:** `date_from` after `date_to`, status `PENDING`, type `REFUND`, date `15.01.2026` → 422. `date_to=9999-12-31` → 200 (regression of BUG-09).

### TC-STM-005 Pagination

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-STM-03 | High | Boundary | `tests/api/test_statement.py::test_pagination`, `tests/api/test_statement.py::test_pagination_out_of_range_422`, `tests/api/test_statement.py::test_huge_offset_422` |

**Steps:** 25 top-ups; default page; `offset=20`; `limit=100`; `limit=1`; `limit=0`, `limit=101`, `offset=-1`, `offset=2^63`.
**Expected result:** 20 items, `total` 25; 5 items; 25; 1; the last four → 422.

### TC-STM-006 Balance consistency

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-STM-04 | Critical | Positive | `tests/db/test_balance_consistency.py::test_balance_equals_sum_of_approved_transactions` |

**Steps:** mixed scenario (approved, wrong CVV, over limit, fraud decline, top-up, minimum commission); SQL check.
**Expected result:** balance = approved top-ups − payments − commissions = 375.36.
