# Security checklist

Focus: authentication, access to other clients' data, card data protection.

## Authentication (BR-AUTH)

- [ ] No token, garbage token, wrong scheme, wrong signature, expired token → 401 — BR-AUTH-03
- [ ] Token of a user that does not exist → 401 — BR-AUTH-03
- [ ] Wrong password and unknown e-mail give the same 401 response — BR-AUTH-02
- [ ] Password is never returned and stored only as a bcrypt hash — BR-AUTH-05
- [ ] Very long password (over 72 bytes) → 401 on login / 422 on register, never 500 — BR-AUTH-01

## Access control / IDOR

For each object, use a second client's token:

- [ ] Account: view, top up, list cards, issue card, statement → 404 — BR-ACC-02
- [ ] Card: view, block, pay → 404 — BR-CARD-03
- [ ] 404 body for a foreign object equals the body for a random UUID — BR-ACC-02

## Card data (NFR-04)

- [ ] Full PAN and CVV only in the issue response — BR-CARD-02
- [ ] Card view and card list show only `**** **** **** 1234` — BR-CARD-03
- [ ] Database: no full PAN, no plaintext CVV; CVV hash is bcrypt — NFR-04
- [ ] PAN hash is keyed (HMAC), not a plain SHA-256 — NFR-04
- [ ] CVV is not part of the idempotency request hash — NFR-04
- [ ] Service logs contain no PAN, CVV or password — NFR-04

## Input robustness (NFR-03)

- [ ] NUL character (`\u0000`) in any text field → 422 — NFR-03
- [ ] Body that is not valid UTF-8 or not JSON → 422 — NFR-03
- [ ] Generated requests (schemathesis) never cause 5xx — NFR-03
