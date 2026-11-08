# BUG-12 CVV in non-Latin digits is counted as a wrong attempt

| Severity | Priority | Status | Requirement | Environment | Found by |
|---|---|---|---|---|---|
| Minor | Low | Open — deferred | BR-PAY-01, BR-CARD-06 | Local stack, http://localhost:8000 | Independent code review |

## Steps to reproduce

1. `POST /payments` with `"cvv": "٣٤٥"` (Arabic-Indic digits).

## Expected

422 — CVV must be 3 digits 0–9.

## Actual

201 DECLINED `INVALID_CVV` and the failure counter increases (regex `\d` matches any Unicode digit).

## Evidence

Manual request; code `wallet-api/app/schemas/payments.py`.

## Notes

Suggested fix: pattern `^[0-9]{3}$`.
