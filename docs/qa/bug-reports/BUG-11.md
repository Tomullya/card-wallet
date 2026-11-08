# BUG-11 CVV recoverable from the idempotency request hash

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Critical | Highest | Closed — fixed and verified | NFR-04, BR-PAY-07 | Local stack, http://localhost:8000 | Independent code review |

## Steps to reproduce

1. Read `idempotency_keys.request_hash` and the linked transaction (card, amount, merchant).
2. Hash the request body with each of the 1000 possible CVVs.

## Expected

The CVV is stored only as a bcrypt hash (BR-CARD-02).

## Actual

The idempotency hash included the CVV — 1000 guesses reveal it.

## Evidence

Regression test `tests/unit/test_idempotency_hash.py::test_request_hash_does_not_depend_on_cvv`.

## Notes

Fix: the CVV is excluded from the hash. Side effect (accepted): a retry with the same key and a different CVV replays the first result.
