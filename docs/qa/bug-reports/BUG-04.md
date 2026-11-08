# BUG-04 GET /cards/{id} returns another client's card (IDOR)

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Critical | Highest | Planted (BUGGY_MODE) | BR-CARD-03 | `wallet-buggy` (BUGGY_MODE=true), http://localhost:8001 | `tests/api/test_cards.py::test_other_users_card_and_account_404` |

## Steps to reproduce

1. Client A issues a card and shares nothing.
2. Client B (own token) calls `GET /cards/{A's card id}`.

## Expected

404 `NOT_FOUND`, same body as for a random id.

## Actual

200 with A's card: masked PAN, expiry, status, daily limit.

## Evidence

`scripts/verify_bugs_caught.py`: BUG-04 caught.

## Notes

Insecure Direct Object Reference — one of the most common API vulnerabilities (OWASP API Security Top 10: Broken Object Level Authorization).
