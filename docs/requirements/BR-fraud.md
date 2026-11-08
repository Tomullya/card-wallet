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
