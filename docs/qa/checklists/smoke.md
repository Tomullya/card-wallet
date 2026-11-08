# Smoke checklist

Run after every deploy, before deeper testing. About 5 minutes in Postman
(collection "Card Wallet API", top to bottom). Stop and report if any item fails.

## Service

- [ ] `GET /health` → 200, `status`, `database` and `fraud_service` are `ok` — NFR-06
- [ ] Swagger opens at `/docs` — NFR-05

## Main flow

- [ ] Register a new client → 201, password not in the response — BR-AUTH-01
- [ ] Log in → 200, token returned — BR-AUTH-02
- [ ] `GET /me` with the token → own profile — BR-AUTH-04
- [ ] Open an EUR account → 201, balance `"0.00"` — BR-ACC-01
- [ ] Top up `100.00` → balance `"100.00"` — BR-ACC-03
- [ ] Issue a card → 201, full PAN and CVV shown once — BR-CARD-02
- [ ] View the card → PAN masked, no CVV — BR-CARD-03
- [ ] Pay `10.00` → APPROVED, commission `"0.50"`, balance `"89.50"` — BR-PAY-05
- [ ] Statement shows top-up, payment and commission, newest first — BR-STM-01

## Integration

- [ ] Payment at a `GAMBLING` merchant → DECLINED `FRAUD_BLOCKED_CATEGORY` — BR-FRD-01
