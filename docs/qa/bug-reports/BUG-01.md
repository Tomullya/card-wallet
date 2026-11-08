# BUG-01 Minimum commission 0.50 is not applied

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Major | High | Planted (BUGGY_MODE) | BR-PAY-03 | `wallet-buggy` (BUGGY_MODE=true), http://localhost:8001 | `tests/api/test_payments.py::test_min_commission_applied` |

## Steps to reproduce

1. Register, log in, open an EUR account, top up `100.00`, issue a card.
2. `POST /payments` with `amount` `"10.00"`.

## Expected

`commission` = `"0.50"` (1 % = 0.10 is below the 0.50 minimum); balance `"89.50"`.

## Actual

`commission` = `"0.10"`; balance `"89.90"`. The bank loses 0.40 on every small payment.

## Evidence

`scripts/verify_bugs_caught.py`: BUG-01 — pass on :8000, fail (caught) on :8001.

## Notes

Planted on purpose to show that the automated suite catches it. Code: `wallet-api/app/services/payments.py`, branch `buggy.enabled("BUG-01")`.
