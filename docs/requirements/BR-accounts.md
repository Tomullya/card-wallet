# BR-ACC — Accounts and top-ups

## BR-ACC-01 Open an account

A client can open an account in one of the supported currencies.

Acceptance criteria:
- Supported currencies: `EUR`, `USD`, `PLN`. Any other value returns `422 VALIDATION_ERROR`.
- A client can have at most **one account per currency**. A second account in the same
  currency returns `409 ACCOUNT_ALREADY_EXISTS`.
- A new account has balance `0.00`.
- Successful creation returns `201` with account id, currency, balance and creation date.

## BR-ACC-02 List and view accounts

Acceptance criteria:
- `GET /api/v1/accounts` returns only the accounts of the current client.
- `GET /api/v1/accounts/{id}` returns one account with its current balance.
- An account of another client returns `404 NOT_FOUND` (see general conventions).

## BR-ACC-03 Top-up

A client can add money to their own account.

Acceptance criteria:
- Amount must be greater than `0.00` and not more than `10000.00`.
- Amount must have at most 2 decimal places (`10.555` is rejected).
- The top-up is always in the account currency (no currency field in the request).
- Invalid amount returns `422 VALIDATION_ERROR`.
- Success returns `201` with the created transaction and the new balance.
- A transaction of type `TOP_UP` with status `APPROVED` is saved.
- The account balance increases by exactly the top-up amount.
