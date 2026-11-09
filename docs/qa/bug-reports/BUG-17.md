# BUG-17 Unknown API key returns PERMISSION_DENIED instead of UNAUTHENTICATED

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Minor | Medium | Planted (BUGGY_MODE) | BR-FRD-04 | `fraud-buggy` (BUGGY_MODE=true), `localhost:50052` | `tests/grpc/test_metadata.py::test_unknown_key_unauthenticated` |

## Steps to reproduce

1. Postman → New → gRPC → `localhost:50052`, method `fraud.v1.FraudService/CheckPayment`.
2. Metadata: `x-api-key` = `wrong`. Message: any valid payment. Invoke.

## Expected

Status `UNAUTHENTICATED` (16): the caller is not identified — the key is unknown.

## Actual

Status `PERMISSION_DENIED` (7). The client is told "you are known but not allowed", so it
cannot tell a typo in the key from a missing permission and may not refresh its credentials.

## Evidence

`scripts/verify_bugs_caught.py`: BUG-17 — pass on :50051, fail (caught) on :50052.

## Notes

Planted on purpose. Code: `fraud-service/fraud_service/auth.py`, branch `buggy.enabled("BUG-17")`.
