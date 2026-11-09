# gRPC deep dive — design

Date: 2026-11-09 · Status: approved in conversation (parts 1–3), awaiting review of this document

## 1. Goal

Turn the Fraud Service from "one unary call" into a complete gRPC showcase and use it as a
hands-on trainer, so the author can explain and test every core gRPC feature in an interview:
all four call types, metadata, deadlines and cancellation, and the status codes a QA engineer
meets in practice.

Success = everything in §8 is true. Deadline: before 2026-12-02 (lab ready in 2–3 days, then
one lesson a day).

Out of scope: TLS, load balancing, showing the event stream in the web app, Kafka / RabbitMQ
(separate pet projects later), load testing.

## 2. Service changes (`proto/fraudpb/fraud.proto`, package `fraud.v1`)

Backward compatible: existing fields and `CheckPayment` behaviour stay; new fields get new numbers.

| RPC | Type | Behaviour |
|---|---|---|
| `CheckPayment(CheckPaymentRequest) → CheckPaymentResponse` | unary (exists) | unchanged rules; now also publishes a `RiskEvent` and stores the decision |
| `GetDecision(GetDecisionRequest) → CheckPaymentResponse` | unary (new) | returns a stored decision by `transaction_id`; unknown id → `NOT_FOUND` |
| `WatchRiskEvents(WatchRiskEventsRequest) → stream RiskEvent` | server streaming | live feed of every decision made after subscribing, filtered by `min_risk_score`; runs until the client cancels or its deadline expires |
| `CheckBatch(stream CheckPaymentRequest) → BatchSummary` | client streaming | evaluates every payment, answers once at the end with totals |
| `ScorePayments(stream CheckPaymentRequest) → stream CheckPaymentResponse` | bidirectional | one response per request, same order, sent as soon as each request is scored; ends when the client closes its side |

New / changed messages:

```proto
message CheckPaymentResponse { Decision decision = 1; string reason = 2; int32 risk_score = 3;
                               string transaction_id = 4; }          // 4 is new: matches bidi answers
message GetDecisionRequest { string transaction_id = 1; }
message WatchRiskEventsRequest { int32 min_risk_score = 1; }         // 0 = all events
message RiskEvent { string transaction_id = 1; string user_id = 2; Decision decision = 3;
                    string reason = 4; int32 risk_score = 5; string amount = 6;
                    string currency = 7; string occurred_at = 8;     // RFC 3339, UTC
                    string request_id = 9; }
message BatchSummary { int32 total = 1; int32 approved = 2; int32 declined = 3;
                       repeated string declined_transaction_ids = 4; }
```

Every decision (from `CheckPayment`, `CheckBatch` or `ScorePayments`) is stored and published.

Internals (in `fraud-service/fraud_service/`):

- `events.py` — in-memory hub: subscribe / unsubscribe / publish. One bounded queue per
  subscriber (1000 events; on overflow the event is dropped for that subscriber and logged).
  At most 8 concurrent subscribers (each holds a server thread).
- `decisions.py` — in-memory store of the last 10 000 decisions (oldest evicted).
- `auth.py` — server interceptor for metadata (§3).
- `server.py` — servicer methods; rules stay in `rules.py`.

## 3. Metadata

| Key | Direction | Rule |
|---|---|---|
| `x-api-key` | client → server | required on every `FraudService` method (not on health or reflection) |
| `x-request-id` | both | optional from the client; the server generates a UUID if absent; always returned in **trailing** metadata (on success and on error) and written to the log line |

Two keys, from environment variables:

| Variable (default for local use) | Role | Allowed methods |
|---|---|---|
| `FRAUD_API_KEY_WALLET` (`dev-wallet-key`) | wallet | all |
| `FRAUD_API_KEY_MONITOR` (`dev-monitor-key`) | monitoring | `WatchRiskEvents`, `GetDecision` |

Missing or unknown key → `UNAUTHENTICATED`. Known key calling a method its role may not use →
`PERMISSION_DENIED`.

Wallet API: `fraud_client.py` sends `x-api-key` (`FRAUD_API_KEY`, default `dev-wallet-key`) and
a new `x-request-id` per call, logged together with the transaction id. docker-compose passes the
keys to both services.

## 4. Status codes covered

| Code | How to get it |
|---|---|
| `OK` | any valid call |
| `INVALID_ARGUMENT` | non-decimal amount (any RPC); `min_risk_score` outside 0–100; empty `CheckBatch` |
| `NOT_FOUND` | `GetDecision` with an unknown transaction id |
| `UNAUTHENTICATED` | no `x-api-key`, or an unknown one |
| `PERMISSION_DENIED` | monitor key calling `CheckPayment`, `CheckBatch` or `ScorePayments` |
| `RESOURCE_EXHAUSTED` | `CheckBatch` with more than 1000 payments; a 9th concurrent `WatchRiskEvents` subscriber |
| `DEADLINE_EXCEEDED` | merchant `TEST_TIMEOUT` (5 s sleep) with a shorter client deadline; a watch stream reaching its deadline |
| `CANCELLED` | the client cancels a stream (`call.cancel()`) |
| `INTERNAL` | merchant `TEST_ERROR` |
| `UNAVAILABLE` | calling a stopped service / wrong port |

A batch or bidi stream with one invalid item is rejected with `INVALID_ARGUMENT`; the message
names the item index (0-based). For `ScorePayments`, answers already sent stay valid.

## 5. Planted gRPC defects (`BUGGY_MODE` for the Fraud Service)

New container `fraud-buggy` (same image, `BUGGY_MODE=true`, host port 50052) in the existing
`buggy` compose profile. Not used by any wallet.

| Bug | Defect | Caught by |
|---|---|---|
| BUG-17 | unknown API key returns `PERMISSION_DENIED` instead of `UNAUTHENTICATED` | metadata test |
| BUG-18 | `ScorePayments` does not end its response stream after the client closes — the call hangs until the deadline | bidi test with a deadline |
| BUG-19 | `x-request-id` is not returned in trailing metadata | metadata test |

`scripts/verify_bugs_caught.py` is extended: each gRPC test runs against 50051 (must pass) and
50052 (must fail). Bug reports BUG-17…19 are added in the existing format.

## 6. Trainer (`docs/grpc-lab/` + `grpc-lab/`)

Lessons, in Russian, one file each: `00-basics` (proto, protobuf, HTTP/2, gRPC vs REST),
`01-unary` (+ reflection), `02-metadata`, `03-status-codes`, `04-deadlines`, `05-server-streaming`,
`06-client-streaming`, `07-bidi`, `08-how-to-test` (strategy, checklist, interview questions).
`docs/grpc-lab/README.md` explains the order and how to check an exercise.

Every lesson has the same sections: **Зачем** (one paragraph, payment example) → **Попробуй в
Postman** (step by step, incl. metadata and streaming) → **Посмотри в коде** (short Python) →
**Задание** → **Вопросы с собеседования** (answers at the end of the file).

Exercises (lessons 1–7): `grpc-lab/exercises/test_lab_0N_<topic>.py` — test skeletons with
`pytest.fail("TODO …")` placeholders and comments saying what to write. Shared fixtures in
`grpc-lab/conftest.py` (channel, stubs, metadata helpers; address from `FRAUD_ADDRESS`, default
`localhost:50051`). Lesson 8 exercise: write a short gRPC test checklist (no auto-check; sample
in solutions). One more exercise: find BUG-17…19 on port 50052 and write the test that catches
each.

`scripts/grpc_lab_check.py N` runs exercise N and prints a short Russian verdict (passed /
which check failed). Reference solutions: `grpc-lab/solutions/` (same file names).

Revision quiz: a separate web page (published artifact, not in the repo) with about 30
questions built from the lessons; made after the lessons are written.

## 7. Testing and CI

- Requirements: new IDs `BR-FRD-04…` in `docs/requirements/BR-fraud.md` (streams, GetDecision,
  metadata/auth, batch limits, subscriber limit, request id). Traceability stays enforced: every
  requirement has at least one tagged test or CI fails.
- Tests in `tests/grpc/`: `test_metadata.py`, `test_status_codes.py`, `test_deadlines.py`,
  `test_server_streaming.py`, `test_client_streaming.py`, `test_bidi_streaming.py`; unit tests
  for `events.py`, `decisions.py`, auth role table in `tests/unit/`.
- `tests/integration/`: a payment made through the REST API appears in `WatchRiskEvents`
  with the same transaction id; `GetDecision` returns it afterwards.
- Every streaming test sets a client deadline (≤ 5 s), so a hanging stream fails instead of
  blocking CI.
- CI (`scripts/ci_local.sh` and `.github/workflows/ci.yml`): runs the new tests; runs
  `grpc-lab/solutions/`; only collects `grpc-lab/exercises/` (must import cleanly, not run).
  The `buggy` profile step now also verifies BUG-17…19.
- Docs: README (gRPC section, test counts, bug table), `docs/api-guide.ru.md` (new gRPC
  section), QA docs (gRPC checklist, test cases for the new RPCs, traceability matrix).

## 8. Done when

1. `scripts/ci_local.sh` ends with "CI OK".
2. CI on GitHub is green after the branch is merged and pushed.
3. All reference solutions pass; every exercise skeleton fails with a TODO message.
4. `verify_bugs_caught.py` reports all planted defects caught, including BUG-17…19.
5. The author has done lesson 0 and said the explanations are clear.
