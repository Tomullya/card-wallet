# BR-PAY — Card payments

## BR-PAY-01 Payment request

A client pays at a (simulated) merchant with their own card.

Request fields:
- `card_id` — the client's card;
- `cvv` — 3 digits;
- `amount` — greater than `0.00`, not more than `10000.00`, at most 2 decimal places;
- `merchant_name` — 1–100 characters;
- `merchant_category` — one of `GROCERIES`, `ELECTRONICS`, `TRAVEL`, `RESTAURANTS`,
  `GAMBLING`, `OTHER`;
- header `Idempotency-Key` — required, 8–64 characters.

Acceptance criteria:
- Payment currency is always the currency of the card's account.
- Invalid fields or a missing `Idempotency-Key` return `422 VALIDATION_ERROR`.
- A card of another client returns `404 NOT_FOUND`.

## BR-PAY-02 Order of checks and decline reasons

The checks run in this order. The first failed check declines the payment.

| # | Check | Decline reason |
|---|---|---|
| 1 | Card is not blocked | `CARD_BLOCKED` |
| 2 | Card is not expired | `CARD_EXPIRED` |
| 3 | CVV is correct (see BR-CARD-06) | `INVALID_CVV` |
| 4 | Balance ≥ amount + commission | `INSUFFICIENT_FUNDS` |
| 5 | Today's approved payments + amount ≤ daily limit | `DAILY_LIMIT_EXCEEDED` |
| 6 | Anti-fraud service approves (see BR-FRD) | `FRAUD_HIGH_AMOUNT`, `FRAUD_BLOCKED_CATEGORY` |

## BR-PAY-03 Commission

Acceptance criteria:
- Commission = 1% of the payment amount, rounded half-up to cents, **minimum `0.50`**.
  Examples: 10.00 → 0.50; 50.00 → 0.50; 100.00 → 1.00; 123.45 → 1.23; 0.01 → 0.50.
- Commission is charged only for approved payments.

## BR-PAY-04 Daily limit

Acceptance criteria:
- The daily limit is per card and per calendar day in UTC.
- Only the payment amounts of `APPROVED` payments count; commission does not count.
- A payment that makes the total **exactly equal** to the limit is allowed.

## BR-PAY-05 Approved payment

Acceptance criteria:
- Response: `201` with `"status": "APPROVED"`.
- Two transactions are saved: `PAYMENT` (amount) and `COMMISSION` (commission),
  both `APPROVED`; the commission transaction refers to the payment transaction.
- The balance decreases by amount + commission in one database transaction
  (either both are charged or nothing is).

## BR-PAY-06 Declined payment

Acceptance criteria:
- Response: `201` with `"status": "DECLINED"` and `decline_reason`.
- One `PAYMENT` transaction with status `DECLINED` and the reason is saved.
- The balance does not change. No commission is charged.

## BR-PAY-07 Idempotency

Acceptance criteria:
- Idempotency keys are unique per client.
- A repeated request with the same key and the same body returns the same response as
  the first request and does not create new transactions or change the balance.
- A repeated request with the same key and a different body returns
  `409 IDEMPOTENCY_KEY_REUSED`.

## BR-PAY-08 Anti-fraud service unavailable

Acceptance criteria:
- If the anti-fraud service does not answer within 2 seconds or returns an error, the
  response is `503 FRAUD_SERVICE_UNAVAILABLE`.
- Nothing is saved, the balance does not change and the idempotency key is not used up,
  so the client can retry with the same key.

## BR-PAY-09 Parallel payments

Acceptance criteria:
- Payments sent in parallel from the same account must never make the balance negative.
- Example: balance 100.00, two parallel payments of 60.00 → exactly one is approved,
  the other is declined with `INSUFFICIENT_FUNDS`.
