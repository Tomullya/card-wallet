# BUG-07 Request body that is not valid UTF-8 returns undocumented 400

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Minor | Medium | Closed — fixed and verified | NFR-03 | Local stack, http://localhost:8000 | Contract tests (status code conformance) |

## Steps to reproduce

1. `POST /auth/login` with header `Content-Type: application/json` and raw body bytes `K\x80`.

## Expected

422 `VALIDATION_ERROR` in the standard error format, like any other invalid input.

## Actual

400 with code `HTTP_ERROR`, not described in the OpenAPI schema.

## Evidence

Regression test `tests/api/test_errors.py::test_malformed_body_is_validation_error`.

## Notes

Fix: the framework's 400 'body could not be parsed' is mapped to 422 VALIDATION_ERROR.
