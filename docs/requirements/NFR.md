# NFR — Non-functional requirements

## NFR-01 Money precision
Money is stored and calculated as decimal numbers with 2 decimal places, never as
floating-point numbers. Rounding is half-up.

## NFR-02 Time
All timestamps are stored and returned in UTC, ISO 8601 format
(for example `2026-11-08T10:15:00Z`).

## NFR-03 Error format
Every error response has the same structure:
```json
{ "error": { "code": "CARD_BLOCKED", "message": "Card is blocked" } }
```
Validation errors may add a `details` list with the field name and problem.

## NFR-04 Sensitive data
- Full PAN and CVV never appear in logs.
- CVV and passwords are stored only as hashes.
- Only fictional data is used (card prefix `400000`).

## NFR-05 API documentation
Interactive OpenAPI (Swagger) documentation is available at `/docs`.

## NFR-06 Health checks
- Wallet API: `GET /api/v1/health` returns `200` and the status of the database and
  the anti-fraud service.
- Anti-fraud service: standard gRPC health check (BR-FRD-03).

## NFR-07 One-command start
The whole system (database, wallet API, anti-fraud service, frontend) starts locally with
`docker compose up`.

## NFR-08 Automated quality checks
All automated tests run in CI on every push, and the test report is published online.

## NFR-09 Interactive trainer site
The gRPC lessons are also published as a public, interactive site
(`https://tomullya.github.io/card-wallet/grpc-lab/`).

Acceptance criteria:
- Nine lessons (00–08), each with comic, theory, diagram, sandbox, quiz and practice tabs.
- Russian and English with identical content keys; light and dark themes.
- Progress is kept in the browser; the site still works when browser storage is blocked.
- Keyboard-operable; animations respect reduced-motion settings.

## NFR-10 Sandbox matches the service
The site's sandbox simulates the Fraud Service. Every sandbox scenario
(`site/grpc-lab/scenarios.json`) gives the same status code and key fields in the simulator and
in the real service (planted-defect scenarios against `fraud-buggy`).
