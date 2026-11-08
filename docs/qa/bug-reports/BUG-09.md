# BUG-09 Statement with date_to=9999-12-31 or a huge offset crashes with 500

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Major | Medium | Closed — fixed and verified | BR-STM-02, BR-STM-03 | Local stack, http://localhost:8000 | Independent code review |

## Steps to reproduce

1. `GET /accounts/{own id}/transactions?date_to=9999-12-31`.
2. `GET /accounts/{own id}/transactions?offset=9223372036854775808`.

## Expected

Step 1 → 200; step 2 → 422.

## Actual

Both → 500 (`OverflowError: date value out of range`; PostgreSQL bigint overflow).

## Evidence

Regression tests `tests/api/test_statement.py::test_max_date_to_is_not_a_server_error` and `tests/api/test_statement.py::test_huge_offset_422`.

## Notes

Fix: no upper date bound at the maximum date; `offset` limited to the bigint range.
