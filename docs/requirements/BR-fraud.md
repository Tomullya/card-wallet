# BR-FRD — Anti-fraud service

The anti-fraud service is a separate application. The wallet calls it over gRPC before
charging a card payment (check 6 in BR-PAY-02).

## BR-FRD-01 Decision rules

The rules are checked in this order:

| # | Condition | Decision | Reason | Risk score |
|---|---|---|---|---|
| 1 | Amount > `5000.00` | `DECLINE` | `HIGH_AMOUNT` | 90 |
| 2 | Merchant category is `GAMBLING` | `DECLINE` | `BLOCKED_CATEGORY` | 80 |
| 3 | Otherwise | `APPROVE` | — | 10 |

Acceptance criteria:
- Amount exactly `5000.00` is approved.
- The wallet maps `HIGH_AMOUNT` → `FRAUD_HIGH_AMOUNT` and `BLOCKED_CATEGORY` →
  `FRAUD_BLOCKED_CATEGORY` decline reasons.
- The same rules apply to every RPC that scores payments: `CheckPayment`, `CheckBatch` and
  `ScorePayments` (BR-FRD-08, BR-FRD-09).

## BR-FRD-02 Test merchants

Special merchant names simulate failures, like test card numbers in payment sandboxes.

| Merchant name | Behaviour |
|---|---|
| `TEST_TIMEOUT` | Answers after 5 seconds (longer than the wallet's 2-second timeout) |
| `TEST_ERROR` | Returns gRPC status `INTERNAL` |

Acceptance criteria:
- Both cases lead to `503 FRAUD_SERVICE_UNAVAILABLE` in the wallet (see BR-PAY-08).

## BR-FRD-03 Service discovery

Acceptance criteria:
- The service supports gRPC server reflection, so tools like Postman and grpcurl can
  list its methods without the `.proto` file.
- The service has a standard gRPC health check.

## BR-FRD-04 Authentication and roles

Every `FraudService` method requires the metadata key `x-api-key`. Health check and
reflection need no key.

| Key (environment variable, local default) | Role | Allowed methods |
|---|---|---|
| `FRAUD_API_KEY_WALLET` (`dev-wallet-key`) | wallet | all |
| `FRAUD_API_KEY_MONITOR` (`dev-monitor-key`) | monitoring | `WatchRiskEvents`, `GetDecision` |

Acceptance criteria:
- Missing or unknown key → `UNAUTHENTICATED`.
- A known key calling a method its role may not use → `PERMISSION_DENIED`.
- The wallet sends its key on every call; payments keep working.

## BR-FRD-05 Request id

Acceptance criteria:
- The client may send `x-request-id`; if it does not, the service generates a UUID.
- The id is always returned in trailing metadata `x-request-id`, on success and on error.
- The id is written to the service log and copied into `RiskEvent.request_id`.

## BR-FRD-06 Decision lookup

Acceptance criteria:
- `GetDecision(transaction_id)` returns the stored decision of any scoring RPC.
- Unknown transaction id → `NOT_FOUND`.
- The last 10 000 decisions are kept; older ones are evicted.
- A decision finished after the client gave up (deadline expired or call cancelled) is not
  stored or published: the wallet has already answered 503 and saved nothing.

## BR-FRD-07 Risk event stream

`WatchRiskEvents` (server streaming) sends every decision made after the client subscribed.

Acceptance criteria:
- Only events with `risk_score >= min_risk_score` are sent; `min_risk_score` outside 0–100 →
  `INVALID_ARGUMENT`.
- The stream runs until the client cancels (`CANCELLED`) or its deadline expires
  (`DEADLINE_EXCEEDED`).
- At most 8 watchers at a time; the 9th → `RESOURCE_EXHAUSTED`. A watcher that disconnects
  frees its slot.
- Each watcher buffers up to 1000 events; on overflow new events are dropped for that watcher.

## BR-FRD-08 Batch check

`CheckBatch` (client streaming) scores every payment it receives and answers once, at the end.

Acceptance criteria:
- The answer has `total`, `approved`, `declined` and the declined transaction ids in order.
- Empty batch → `INVALID_ARGUMENT`; more than 1000 payments → `RESOURCE_EXHAUSTED`.
- One invalid payment → `INVALID_ARGUMENT` naming its index (0-based); nothing from that batch
  is stored or published. The same holds when any payment fails (e.g. `TEST_ERROR` → `INTERNAL`).

## BR-FRD-09 Live scoring

`ScorePayments` (bidirectional streaming) answers each payment as soon as it is scored.

Acceptance criteria:
- One answer per payment, in the same order, with `transaction_id` copied from the request.
- The response stream ends as soon as the client closes its side.
- An invalid payment → `INVALID_ARGUMENT` naming its index; answers already sent stay valid.
- At most 16 `CheckBatch` and `ScorePayments` calls are open at a time; the next one →
  `RESOURCE_EXHAUSTED`. Open streams and watchers never block single calls such as the
  wallet's `CheckPayment`.
