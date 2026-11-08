# BR-CARD — Cards

## BR-CARD-01 Issue a card

A client can issue a virtual card for their own account.

Acceptance criteria:
- An account can have at most **3 active cards**. Issuing a 4th active card returns
  `409 CARD_LIMIT_REACHED`. Blocked and expired cards do not count.
- An account of another client returns `404 NOT_FOUND`.
- Success returns `201`.

## BR-CARD-02 Card data at issuing

Acceptance criteria:
- PAN is 16 digits, starts with the fictional prefix `400000` and passes the Luhn check.
- Expiry date is the last day of the month, 3 years after the issue month
  (issued in November 2026 → valid until 30 November 2029). Shown as `MM/YY`.
- CVV is 3 random digits.
- **Full PAN and CVV are returned only once**, in the issue response.
- CVV is stored only as a hash.
- Daily limit: optional in the request, from `1.00` to `5000.00`; default `1000.00`.
- A new card has status `ACTIVE`.

## BR-CARD-03 View a card

Acceptance criteria:
- `GET /api/v1/cards/{id}` returns masked PAN in the format `**** **** **** 1234`,
  expiry, status, block reason (if any) and daily limit.
- `GET /api/v1/accounts/{id}/cards` returns all cards of the client's own account in the
  same masked format.
- CVV is never returned after issuing.
- A card or account of another client returns `404 NOT_FOUND`.

## BR-CARD-04 Block a card by client

Acceptance criteria:
- The owner can block an `ACTIVE` card. Status becomes `BLOCKED`,
  block reason `BLOCKED_BY_CLIENT`.
- Blocking an already blocked card returns `409 CARD_ALREADY_BLOCKED`.
- Unblocking is not supported in this version.

## BR-CARD-05 Expired card

Acceptance criteria:
- A card is expired when the current UTC date is after its expiry date.
- An expired card is shown with status `EXPIRED`.

## BR-CARD-06 Block after 3 wrong CVV attempts

Acceptance criteria:
- A payment with a wrong CVV is declined with reason `INVALID_CVV` and increases the
  card's failed-attempt counter by 1.
- After **3 wrong CVV attempts in a row**, the card becomes `BLOCKED` with block reason
  `TOO_MANY_FAILED_ATTEMPTS`. The 3rd attempt itself is declined with `INVALID_CVV`.
- An approved payment resets the counter to 0.
- Payments declined for other reasons (insufficient funds, limit, anti-fraud) do not
  change the counter.
- Attempts on an already blocked card are declined with `CARD_BLOCKED` and do not
  change the counter.
