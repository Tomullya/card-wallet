# Business Requirements — Mini Card Wallet

Mini Card Wallet is a demo fintech application: clients open multi-currency accounts,
issue virtual cards and pay with them. Every card payment is checked by a separate
anti-fraud service.

All data in this project is fictional. Card numbers are generated in a fake range and
are not real payment cards.

## Documents

| File | Area | ID prefix |
|---|---|---|
| [BR-auth.md](BR-auth.md) | Registration, login, access | `BR-AUTH` |
| [BR-accounts.md](BR-accounts.md) | Accounts and top-ups | `BR-ACC` |
| [BR-cards.md](BR-cards.md) | Card issuing, blocking, CVV attempts | `BR-CARD` |
| [BR-payments.md](BR-payments.md) | Card payments, commission, limits, idempotency | `BR-PAY` |
| [BR-statement.md](BR-statement.md) | Transaction history | `BR-STM` |
| [BR-fraud.md](BR-fraud.md) | Anti-fraud service | `BR-FRD` |
| [NFR.md](NFR.md) | Non-functional requirements | `NFR` |

## How to read a requirement

Each requirement has:

- **ID** — a stable identifier, used in test cases, bug reports and the traceability matrix;
- **Statement** — what the system must do;
- **Acceptance criteria** — concrete, checkable conditions.

## Glossary

| Term | Meaning |
|---|---|
| Client | A registered user of the wallet |
| Account | A balance in one currency (EUR, USD or PLN) that belongs to a client |
| Card | A virtual payment card linked to one account |
| PAN | Primary Account Number — the 16-digit card number |
| CVV | 3-digit security code of the card |
| Transaction | Any money movement: top-up, payment or commission |
| Approved / Declined | Final status of a payment attempt |
| Decline reason | Machine-readable code that explains why a payment was declined |
| Idempotency key | A unique key sent with a payment so that a retry does not charge twice |
| Daily limit | Maximum total amount of approved payments per card per calendar day (UTC) |
| Anti-fraud service | A separate service that approves or declines a payment before money is charged |

## General conventions

- Money amounts have exactly 2 decimal places. Rounding is half-up (0.005 → 0.01).
- All dates and times are in UTC.
- A client can only see and use their own accounts, cards and transactions.
- Requests for objects that do not exist **or** belong to another client return `404`
  with the same response, so the API does not reveal that the object exists.
