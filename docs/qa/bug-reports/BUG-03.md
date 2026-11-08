# BUG-03 CVV failure counter is not reset after an approved payment

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Major | High | Planted (BUGGY_MODE) | BR-CARD-06 | `wallet-buggy` (BUGGY_MODE=true), http://localhost:8001 | `tests/api/test_cvv_attempts.py::test_success_resets_counter` |

## Steps to reproduce

1. Pay with a wrong CVV twice.
2. Pay with the correct CVV → APPROVED.
3. Pay with a wrong CVV twice more.
4. `GET /cards/{id}`.

## Expected

Card `ACTIVE` — the approved payment reset the counter, so only 2 failures in a row.

## Actual

Card `BLOCKED` / `TOO_MANY_FAILED_ATTEMPTS` after the 3rd wrong CVV overall. A real client gets blocked for occasional typos.

## Evidence

`scripts/verify_bugs_caught.py`: BUG-03 caught.

## Notes

State-transition defect: found only by a test that checks the sequence, not single requests.
