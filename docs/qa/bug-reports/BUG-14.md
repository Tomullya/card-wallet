# BUG-14 Lower-case 'bearer' authorization scheme is rejected

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Minor | Low | Open — deferred | BR-AUTH-03 | Local stack, http://localhost:8000 | Independent code review |

## Steps to reproduce

1. `GET /me` with header `Authorization: bearer <valid token>`.

## Expected

200 — the auth scheme is case-insensitive (RFC 7235).

## Actual

401 `UNAUTHORIZED`.

## Evidence

Manual request; code `wallet-api/app/deps.py`.

## Notes

Most clients send `Bearer`, so impact is low.
