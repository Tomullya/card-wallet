# QA documentation

| Document | What it is |
|---|---|
| [Test plan](test-plan.md) | Scope, approach, test levels, environments, entry/exit criteria, risks |
| [Test cases](test-cases/) | 50 test cases by area, each linked to requirements and to the automated test |
| [Checklists](checklists/) | [Smoke](checklists/smoke.md), [payments regression](checklists/payments-regression.md), [security](checklists/security.md), [gRPC](checklists/grpc.md) |
| [Bug reports](bug-reports/README.md) | 19 reports: 7 planted (4 REST, 3 gRPC), 7 found and fixed, 5 open |
| [Traceability matrix](traceability-matrix.md) | Requirement → automated tests, generated from test tags |

Checks that keep these documents honest (run in CI):

```bash
.venv/bin/python scripts/traceability.py      # every requirement has a test; matrix regenerated
.venv/bin/python scripts/check_docs.py        # every requirement / test named here exists
.venv/bin/python scripts/verify_bugs_caught.py  # every planted defect is caught
```
