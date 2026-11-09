# BUG-18 ScorePayments does not end its response stream after the client closes

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Major | High | Planted (BUGGY_MODE) | BR-FRD-09 | `fraud-buggy` (BUGGY_MODE=true), `localhost:50052` | `tests/grpc/test_bidi_streaming.py::test_stream_ends_after_client_closes` |

## Steps to reproduce

1. Postman → gRPC → `localhost:50052`, method `ScorePayments`, metadata `x-api-key` = `dev-wallet-key`.
2. Send two payments, then press **End streaming**.

## Expected

Two answers, then the call ends with `OK`.

## Actual

Two answers arrive, but the call stays open until the client deadline and ends with
`DEADLINE_EXCEEDED`. Without a deadline it never ends and holds a server thread.

## Evidence

`scripts/verify_bugs_caught.py`: BUG-18 — pass on :50051, fail (caught) on :50052.

## Notes

Planted on purpose. Code: `fraud-service/fraud_service/server.py`, `ScorePayments`, branch
`buggy.enabled("BUG-18")`. Lesson: always give stream tests a deadline.
