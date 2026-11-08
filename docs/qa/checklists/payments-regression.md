# Payments regression checklist

Run before a release that touches payments, cards or accounts. Each line names the
requirement; most are also automated (see the [traceability matrix](../traceability-matrix.md)).

## Validation (BR-PAY-01)

- [ ] Missing `Idempotency-Key` → 422 — BR-PAY-01
- [ ] `Idempotency-Key` of 7 and 65 characters → 422; 8 and 64 → accepted — BR-PAY-01
- [ ] CVV `12`, `1234`, `abc` → 422 — BR-PAY-01
- [ ] Amount `0`, `10000.01`, `1.001` → 422 — BR-PAY-01
- [ ] Unknown merchant category → 422 — BR-PAY-01
- [ ] Another client's card → 404, owner's balance unchanged — BR-PAY-01

## Check order (BR-PAY-02)

- [ ] Blocked card → `CARD_BLOCKED` — BR-PAY-02
- [ ] Expired card → `CARD_EXPIRED` — BR-PAY-02
- [ ] Blocked **and** expired card → `CARD_BLOCKED` (first check wins) — BR-PAY-02
- [ ] Balance 100.00, pay 99.50 → `INSUFFICIENT_FUNDS` (needs 100.50 with commission) — BR-PAY-02
- [ ] Balance 100.00, pay 99.00 → APPROVED (needs 99.99) — BR-PAY-02

## Commission (BR-PAY-03)

- [ ] 10.00 → 0.50 (minimum) — BR-PAY-03
- [ ] 100.00 → 1.00 — BR-PAY-03
- [ ] 150.50 → 1.51 (half-up rounding) — BR-PAY-03
- [ ] Declined payment → no commission — BR-PAY-06

## Daily limit (BR-PAY-04)

- [ ] Limit 100.00: pay 60.00 + 40.00 → both APPROVED (exact limit allowed) — BR-PAY-04
- [ ] Then 0.01 → `DAILY_LIMIT_EXCEEDED` — BR-PAY-04
- [ ] Commission does not count against the limit — BR-PAY-04
- [ ] Declined payments do not count — BR-PAY-04
- [ ] Yesterday's payments (UTC) do not count — BR-PAY-04

## CVV attempts (BR-CARD-06)

- [ ] 3 wrong CVV in a row → card BLOCKED, `TOO_MANY_FAILED_ATTEMPTS` — BR-CARD-06
- [ ] 2 wrong, 1 correct, 2 wrong → card stays ACTIVE (counter reset) — BR-CARD-06
- [ ] Insufficient funds between wrong attempts does not reset or increase the counter — BR-CARD-06

## Results and storage

- [ ] Approved → two transactions: PAYMENT and COMMISSION linked to it — BR-PAY-05
- [ ] Declined → one DECLINED PAYMENT with the reason, balance unchanged — BR-PAY-06
- [ ] Balance = approved top-ups − payments − commissions — BR-STM-04

## Idempotency and concurrency

- [ ] Same key, same body twice → same response, charged once — BR-PAY-07
- [ ] Same key, different amount → 409 `IDEMPOTENCY_KEY_REUSED` — BR-PAY-07
- [ ] Same key used by two clients → independent payments — BR-PAY-07
- [ ] Balance 100.00, two parallel payments of 60.00 → one APPROVED, one `INSUFFICIENT_FUNDS` — BR-PAY-09

## Fraud service

- [ ] Amount 5000.01 → `FRAUD_HIGH_AMOUNT`; 5000.00 → APPROVED — BR-FRD-01
- [ ] Merchant `TEST_TIMEOUT` → 503 in under 4 s, nothing saved — BR-PAY-08
- [ ] Merchant `TEST_ERROR` → 503 — BR-FRD-02
- [ ] After a 503 the same key can be used again — BR-PAY-08
