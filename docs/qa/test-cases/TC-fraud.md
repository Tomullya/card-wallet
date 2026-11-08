# Test cases — Anti-fraud service (BR-FRD) and integration

### TC-FRD-001 Decision rules

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-01 | High | Decision table | `tests/unit/test_fraud_rules.py::test_evaluate`, `tests/grpc/test_fraud_service.py::test_approve`, `tests/grpc/test_fraud_service.py::test_decline_high_amount`, `tests/grpc/test_fraud_service.py::test_decline_gambling` |

**Expected result:** 5000.00 → APPROVE (risk 10); 5000.01 → DECLINE HIGH_AMOUNT (90); GAMBLING → DECLINE BLOCKED_CATEGORY (80); 6000.00 + GAMBLING → HIGH_AMOUNT (rule order).

### TC-FRD-002 Fraud decline through the wallet

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-01, BR-PAY-02 | High | Integration | `tests/integration/test_fraud_integration.py::test_high_amount_declined_by_fraud`, `tests/integration/test_fraud_integration.py::test_gambling_declined` |

**Steps:** balance 20000.00, card limit 10000.00: pay 5000.01, then 5000.00. Separately pay at a GAMBLING merchant.
**Expected result:** `FRAUD_HIGH_AMOUNT` with balance unchanged; 5000.00 APPROVED; gambling → `FRAUD_BLOCKED_CATEGORY`.

### TC-FRD-003 Fraud service timeout

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-08, BR-FRD-02 | Critical | Integration / negative | `tests/integration/test_fraud_integration.py::test_timeout_returns_503_and_saves_nothing`, `tests/grpc/test_fraud_service.py::test_test_timeout_exceeds_2s_deadline` |

**Steps:** pay at merchant `TEST_TIMEOUT`.
**Expected result:** 503 `FRAUD_SERVICE_UNAVAILABLE` in under 4 s; no new transactions; balance unchanged.

### TC-FRD-004 Fraud service error and retry

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-PAY-08, BR-FRD-02 | High | Integration / negative | `tests/integration/test_fraud_integration.py::test_error_returns_503`, `tests/api/test_idempotency.py::test_key_reusable_after_503` |

**Steps:** pay at `TEST_ERROR` with key K; then pay at "Shop" with the same key K.
**Expected result:** 503; then 201 APPROVED (the key was not used up).

### TC-FRD-005 Reflection and health

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-03, NFR-06 | Medium | Positive | `tests/grpc/test_fraud_service.py::test_reflection_lists_service`, `tests/grpc/test_fraud_service.py::test_health_serving`, `tests/api/test_health.py::test_health_reports_fraud_service_ok` |

**Steps:** in Postman: New → gRPC → `localhost:50051`; list methods. Call the gRPC health check. Call `GET /health` on the wallet.
**Expected result:** `fraud.v1.FraudService` listed; health SERVING; wallet health shows `fraud_service: ok`.
