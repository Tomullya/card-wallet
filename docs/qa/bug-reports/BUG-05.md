# BUG-05 Requirements defect: fraud rule 'amount > 5000' could never trigger

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Major | High | Closed — fixed and verified | BR-CARD-02, BR-FRD-01, BR-PAY-02 | Requirements review (before implementation) | Requirements analysis while writing the implementation plan |

## Steps to reproduce

1. Read BR-CARD-02: card daily limit at most 5000.00.
2. Read BR-FRD-01: anti-fraud declines amounts above 5000.00.
3. Read BR-PAY-02: the daily-limit check runs before the anti-fraud check.

## Expected

Every business rule can be reached and tested.

## Actual

Any payment above 5000.00 is always declined by the daily limit first, so `FRAUD_HIGH_AMOUNT` is unreachable.

## Evidence

Plan 1 history note; regression test `tests/integration/test_fraud_integration.py::test_high_amount_declined_by_fraud`.

## Notes

Fix: maximum card daily limit raised to 10000.00 (equal to the maximum payment). Cheapest kind of defect — found before any code existed.
