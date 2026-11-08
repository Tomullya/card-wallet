# Bug reports

| Group | Bugs | What it shows |
|---|---|---|
| Planted (BUGGY_MODE) | BUG-01 … BUG-04 | Each is caught by a specific automated test — `scripts/verify_bugs_caught.py` proves it |
| Found and fixed | BUG-05 … BUG-11 | Found by requirements review, contract tests and code review; each has a regression test |
| Open (deferred) | BUG-12 … BUG-16 | Known minor issues, prioritised and documented |

Severity scale: see the [test plan](../test-plan.md#7-defect-management).

| ID | Title | Severity | Status | Requirement |
|---|---|---|---|---|
| [BUG-01](BUG-01.md) | Minimum commission 0.50 is not applied | Major | Planted (BUGGY_MODE) | BR-PAY-03 |
| [BUG-02](BUG-02.md) | Payment that reaches the daily limit exactly is declined | Major | Planted (BUGGY_MODE) | BR-PAY-04 |
| [BUG-03](BUG-03.md) | CVV failure counter is not reset after an approved payment | Major | Planted (BUGGY_MODE) | BR-CARD-06 |
| [BUG-04](BUG-04.md) | GET /cards/{id} returns another client's card (IDOR) | Critical | Planted (BUGGY_MODE) | BR-CARD-03 |
| [BUG-05](BUG-05.md) | Requirements defect: fraud rule 'amount > 5000' could never trigger | Major | Closed — fixed and verified | BR-CARD-02, BR-FRD-01, BR-PAY-02 |
| [BUG-06](BUG-06.md) | Login with a password longer than 72 bytes crashes with 500 | Critical | Closed — fixed and verified | BR-AUTH-02, BR-AUTH-01 |
| [BUG-07](BUG-07.md) | Request body that is not valid UTF-8 returns undocumented 400 | Minor | Closed — fixed and verified | NFR-03 |
| [BUG-08](BUG-08.md) | NUL character in a text field crashes with 500 | Critical | Closed — fixed and verified | NFR-03, BR-AUTH-01, BR-PAY-01 |
| [BUG-09](BUG-09.md) | Statement with date_to=9999-12-31 or a huge offset crashes with 500 | Major | Closed — fixed and verified | BR-STM-02, BR-STM-03 |
| [BUG-10](BUG-10.md) | Full card number recoverable from its stored hash | Critical | Closed — fixed and verified | NFR-04, BR-CARD-02 |
| [BUG-11](BUG-11.md) | CVV recoverable from the idempotency request hash | Critical | Closed — fixed and verified | NFR-04, BR-PAY-07 |
| [BUG-12](BUG-12.md) | CVV in non-Latin digits is counted as a wrong attempt | Minor | Open — deferred | BR-PAY-01, BR-CARD-06 |
| [BUG-13](BUG-13.md) | An expired card can still be blocked by the client | Trivial | Open — deferred | BR-CARD-04 |
| [BUG-14](BUG-14.md) | Lower-case 'bearer' authorization scheme is rejected | Minor | Open — deferred | BR-AUTH-03 |
| [BUG-15](BUG-15.md) | Request duration is not logged | Trivial | Open — deferred | NFR-06 |
| [BUG-16](BUG-16.md) | Slow fraud calls can starve the fraud service | Minor | Open — deferred | BR-PAY-08, BR-FRD-02 |

## Try the planted defects yourself

```bash
docker compose --profile buggy up -d      # wallet-buggy on port 8001
.venv/bin/python scripts/verify_bugs_caught.py
```
