# Checklist — gRPC Fraud Service

Run against `localhost:50051` (Postman: New → gRPC, reflection, metadata `x-api-key`).

**Contract**
- [ ] Reflection lists `fraud.v1.FraudService` with 5 methods (BR-FRD-03)
- [ ] Health check `SERVING` without a key (BR-FRD-03, BR-FRD-04)

**Metadata**
- [ ] No key / unknown key → `UNAUTHENTICATED`; monitor key on `CheckPayment` → `PERMISSION_DENIED` (BR-FRD-04)
- [ ] `x-request-id` returned in trailers, also on errors (BR-FRD-05)

**Unary**
- [ ] 5000.00 approved, 5000.01 declined `HIGH_AMOUNT`, `GAMBLING` declined (BR-FRD-01)
- [ ] `GetDecision` finds a scored payment; unknown id → `NOT_FOUND` (BR-FRD-06)

**Streams**
- [ ] `WatchRiskEvents`: a payment on the web site appears; `min_risk_score` filters; 101 → `INVALID_ARGUMENT` (BR-FRD-07)
- [ ] 9th watcher → `RESOURCE_EXHAUSTED`; after cancelling, new watchers connect (BR-FRD-07)
- [ ] `CheckBatch`: totals correct; 1001 items → `RESOURCE_EXHAUSTED`; one bad item → whole batch rejected (BR-FRD-08)
- [ ] `ScorePayments`: answer per payment, same order; ends `OK` after End streaming (BR-FRD-09)

**Time**
- [ ] `TEST_TIMEOUT` with a 1 s deadline → `DEADLINE_EXCEEDED`; through the wallet → `503` (BR-FRD-02, BR-PAY-08)
- [ ] `TEST_ERROR` → `INTERNAL` (BR-FRD-02)
