# BUG-13 An expired card can still be blocked by the client

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Trivial | Low | Open — deferred | BR-CARD-04 | Local stack, http://localhost:8000 | Independent code review |

## Steps to reproduce

1. Set a card's `expiry_date` to yesterday (card shows `EXPIRED`).
2. `POST /cards/{id}/block`.

## Expected

BR-CARD-04 speaks only of ACTIVE cards: 409 or a clear rule.

## Actual

200; card becomes `BLOCKED` / `BLOCKED_BY_CLIENT`.

## Evidence

Manual request.

## Notes

Harmless; needs a product decision (requirements question) rather than a code change.
