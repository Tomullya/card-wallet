# BUG-16 Slow fraud calls can starve the fraud service

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Minor | Low | Open — deferred | BR-PAY-08, BR-FRD-02 | Local stack, http://localhost:8000 | Independent code review |

## Steps to reproduce

1. Send about 16 payments at merchant `TEST_TIMEOUT` in parallel.
2. Meanwhile send a normal payment.

## Expected

The normal payment is checked normally.

## Actual

Expected to get 503: each `TEST_TIMEOUT` call holds one of 16 worker threads for 5 s.

## Evidence

Code `fraud-service/fraud_service/server.py` (`max_workers=16`). Not reproduced yet — needs a load test.

## Notes

Acceptable for a demo; a candidate for the k6 load test.
