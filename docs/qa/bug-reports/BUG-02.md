# BUG-02 Payment that reaches the daily limit exactly is declined

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Major | High | Planted (BUGGY_MODE) | BR-PAY-04 | `wallet-buggy` (BUGGY_MODE=true), http://localhost:8001 | `tests/api/test_payments.py::test_daily_limit_exact_allowed` |

## Steps to reproduce

1. Issue a card with `daily_limit` `"100.00"` on an account with balance 1000.00.
2. Pay `60.00` → APPROVED.
3. Pay `40.00`.

## Expected

APPROVED — the total equals the limit, which BR-PAY-04 allows.

## Actual

DECLINED `DAILY_LIMIT_EXCEEDED` (the check behaves like `>=` instead of `>`).

## Evidence

`scripts/verify_bugs_caught.py`: BUG-02 caught.

## Notes

Classic off-by-one at a boundary — exactly what boundary-value analysis is for.
