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

### TC-FRD-006 API key and roles

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-04 | Critical | Security / negative | `tests/grpc/test_metadata.py::test_missing_key_unauthenticated`, `tests/grpc/test_metadata.py::test_unknown_key_unauthenticated`, `tests/grpc/test_metadata.py::test_monitor_key_cannot_check_payment`, `tests/grpc/test_server_streaming.py::test_monitor_key_may_watch_and_lookup` |

**Steps:** call `CheckPayment` with no key, key `wrong`, the monitor key; call `WatchRiskEvents` and `GetDecision` with the monitor key.
**Expected result:** `UNAUTHENTICATED`, `UNAUTHENTICATED`, `PERMISSION_DENIED`; monitor calls succeed.

### TC-FRD-007 Request id round trip

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-05 | Medium | Observability | `tests/grpc/test_metadata.py::test_request_id_echoed_in_trailers`, `tests/grpc/test_metadata.py::test_request_id_on_error`, `tests/grpc/test_server_streaming.py::test_request_id_reaches_risk_event` |

**Expected result:** the sent `x-request-id` comes back in trailers (also on errors) and in `RiskEvent.request_id`; without one the service returns a UUID.

### TC-FRD-008 Risk event stream

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-07 | High | Streaming / limits | `tests/grpc/test_server_streaming.py::test_watch_receives_new_decision`, `tests/grpc/test_server_streaming.py::test_watch_filters_by_min_score`, `tests/grpc/test_server_streaming.py::test_ninth_watcher_resource_exhausted`, `tests/grpc/test_server_streaming.py::test_cancelled_watchers_free_their_slots`, `tests/integration/test_risk_stream.py::test_rest_payment_appears_in_risk_stream` |

**Steps:** subscribe with `min_risk_score` 0 and 50; pay on the web site; open 9 watchers; cancel 8 and reconnect.
**Expected result:** the payment's event arrives; low-risk events are filtered; the 9th watcher gets `RESOURCE_EXHAUSTED`; freed slots can be reused.

### TC-FRD-009 Batch check

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-08 | High | Boundary / negative | `tests/grpc/test_client_streaming.py::test_batch_summary`, `tests/grpc/test_client_streaming.py::test_batch_of_exactly_1000_allowed`, `tests/grpc/test_client_streaming.py::test_batch_over_limit_resource_exhausted`, `tests/grpc/test_client_streaming.py::test_invalid_item_rejects_whole_batch` |

**Expected result:** totals and declined ids in order; 1000 allowed, 1001 → `RESOURCE_EXHAUSTED`; one bad amount → `INVALID_ARGUMENT` with its index and nothing stored.

### TC-FRD-010 Live scoring

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-09 | High | Streaming | `tests/grpc/test_bidi_streaming.py::test_one_answer_per_request_in_order`, `tests/grpc/test_bidi_streaming.py::test_answer_arrives_before_next_request`, `tests/grpc/test_bidi_streaming.py::test_stream_ends_after_client_closes`, `tests/grpc/test_bidi_streaming.py::test_invalid_item_ends_stream` |

**Expected result:** one answer per payment in order, sent before the next payment arrives; the call ends `OK` when the client closes; a bad item ends it with `INVALID_ARGUMENT`.

### TC-FRD-011 Decision lookup

| Requirement | Priority | Type | Automated by |
|---|---|---|---|
| BR-FRD-06 | Medium | Functional | `tests/grpc/test_server_streaming.py::test_get_decision_found`, `tests/grpc/test_server_streaming.py::test_get_decision_not_found`, `tests/unit/test_fraud_events.py::test_store_evicts_oldest` |

**Expected result:** a scored transaction is returned unchanged; an unknown id → `NOT_FOUND`.

