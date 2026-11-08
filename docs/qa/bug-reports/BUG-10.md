# BUG-10 Full card number recoverable from its stored hash

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Critical | Highest | Closed — fixed and verified | NFR-04, BR-CARD-02 | Local stack, http://localhost:8000 | Independent code review (proof script recovered a PAN in 0.18 s) |

## Steps to reproduce

1. Read a row of the `cards` table: `pan_last4` and `pan_hash`.
2. Try all 10^6 numbers `400000 + 6 digits + last4`, compare SHA-256 with `pan_hash`.

## Expected

The full PAN cannot be recovered from the database (design §3).

## Actual

Plain SHA-256 of a number with only 6 unknown digits — recovered in under a second.

## Evidence

Regression tests `tests/db/test_cards_storage.py::test_pan_hash_is_keyed_not_plain_sha256` and `tests/unit/test_card_numbers.py::test_pan_hash_is_keyed_hmac`.

## Notes

Fix: HMAC-SHA256 with a server-side secret (`CARD_HASH_SECRET`).
