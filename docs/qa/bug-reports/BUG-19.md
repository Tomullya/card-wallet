# BUG-19 x-request-id is not returned in trailing metadata

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Minor | Medium | Planted (BUGGY_MODE) | BR-FRD-05 | `fraud-buggy` (BUGGY_MODE=true), `localhost:50052` | `tests/grpc/test_metadata.py::test_request_id_echoed_in_trailers` |

## Steps to reproduce

1. Postman → gRPC → `localhost:50052`, method `CheckPayment`.
2. Metadata: `x-api-key` = `dev-wallet-key`, `x-request-id` = `lab-123`. Valid payment. Invoke.
3. Open the **Trailers** tab of the response.

## Expected

Trailer `x-request-id: lab-123`.

## Actual

No `x-request-id` trailer on any call except authentication errors (`UNAUTHENTICATED`,
`PERMISSION_DENIED`). Support cannot match a client's request to the service log line.

## Evidence

`scripts/verify_bugs_caught.py`: BUG-19 — pass on :50051, fail (caught) on :50052.

## Notes

Planted on purpose. Code: `fraud-service/fraud_service/auth.py`, branch `buggy.enabled("BUG-19")`.
