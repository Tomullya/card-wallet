# BUG-06 Login with a password longer than 72 bytes crashes with 500

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Critical | High | Closed — fixed and verified | BR-AUTH-02, BR-AUTH-01 | Local stack, http://localhost:8000 | Contract tests (schemathesis), `tests/contract/test_openapi.py::test_api_conforms_to_schema` |

## Steps to reproduce

1. `POST /auth/login` with any e-mail and a password of 100 characters.

## Expected

401 `INVALID_CREDENTIALS`.

## Actual

500 `INTERNAL_ERROR`; log: `ValueError: password cannot be longer than 72 bytes` (bcrypt limit). Registration had the same problem with 72 Cyrillic characters (144 bytes).

## Evidence

Regression tests `tests/api/test_auth.py::test_login_with_very_long_password_401_not_500` and `tests/api/test_auth.py::test_register_password_over_72_bytes_422_not_500`.

## Notes

Fix: passwords over 72 bytes never match on login and are rejected with 422 on registration.
