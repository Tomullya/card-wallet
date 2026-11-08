# BR-STM — Transaction history (statement)

## BR-STM-01 List transactions of an account

Acceptance criteria:
- `GET /api/v1/accounts/{id}/transactions` returns transactions of the client's own account.
- An account of another client returns `404 NOT_FOUND`.
- Sorted by creation time, newest first.
- Each item contains: id, type (`TOP_UP`, `PAYMENT`, `COMMISSION`), amount, currency,
  status (`APPROVED`, `DECLINED`), decline reason, merchant name, last 4 digits of the
  card (for card transactions) and creation time.

## BR-STM-02 Filters

Acceptance criteria:
- Optional filters: `date_from`, `date_to` (inclusive, format `YYYY-MM-DD`), `status`, `type`.
- `date_from` later than `date_to` returns `422 VALIDATION_ERROR`.
- Unknown status or type returns `422 VALIDATION_ERROR`.

## BR-STM-03 Pagination

Acceptance criteria:
- Parameters `limit` (default 20, from 1 to 100) and `offset` (default 0, ≥ 0).
- Values out of range return `422 VALIDATION_ERROR`.
- The response contains `items`, `total` (number of matching transactions), `limit`, `offset`.

## BR-STM-04 Balance consistency

Acceptance criteria:
- The account balance always equals:
  sum of approved `TOP_UP` − sum of approved `PAYMENT` − sum of approved `COMMISSION`.
