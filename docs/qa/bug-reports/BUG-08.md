# BUG-08 NUL character in a text field crashes with 500

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Critical | High | Closed — fixed and verified | NFR-03, BR-AUTH-01, BR-PAY-01 | Local stack, http://localhost:8000 | Contract tests (full run) |

## Steps to reproduce

1. `POST /auth/login` with `{"email": "a\u0000@example.com", "password": "Passw0rd!"}`.

## Expected

422 `VALIDATION_ERROR` (or 401).

## Actual

500; log: `PostgreSQL text fields cannot contain NUL (0x00) bytes`. Same for `name` on registration and `merchant_name` on payments.

## Evidence

Regression tests `tests/api/test_errors.py::test_nul_character_in_login_is_validation_error`, `tests/api/test_errors.py::test_nul_character_in_name_is_validation_error`, `tests/api/test_errors.py::test_nul_character_in_merchant_is_validation_error`.

## Notes

Fix: every request model rejects NUL characters.
