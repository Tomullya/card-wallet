# BUG-15 Request duration is not logged

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Trivial | Low | Open — deferred | NFR-06 | Local stack, http://localhost:8000 | Plan review (planned middleware replaced by the server access log) |

## Steps to reproduce

1. Send any request.
2. `docker compose logs wallet`.

## Expected

Each request logged with method, path, status and duration.

## Actual

Method, path and status only.

## Evidence

Service logs.

## Notes

Matters for performance investigation; not a functional defect.
