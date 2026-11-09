"""The site's sandbox scenarios against the real Fraud Service (NFR-10).

site/grpc-lab/tests/sim.test.mjs runs the same scenarios.json against the simulator, so both
agree with the same expectations — the sandbox cannot teach something the service does not do.
"""

import json
import os
import threading
import uuid
from pathlib import Path

import grpc
import pytest
from fraudpb import fraud_pb2
from fraudpb.fraud_pb2_grpc import FraudServiceStub

from tests.conftest import FRAUD_ADDR, MONITOR_KEY, WALLET_KEY
from tests.grpc.test_limits import IdleStream
from tests.grpc_helpers import Watcher

SCENARIOS = json.loads(
    (Path(__file__).resolve().parents[2] / "site/grpc-lab/scenarios.json").read_text()
)
NORMAL = [s for s in SCENARIOS if not s.get("buggy")]
BUGGY = [s for s in SCENARIOS if s.get("buggy")]
BUGGY_ADDR = os.getenv("BUGGY_FRAUD_ADDR", "localhost:50052")
SEALS = {"wallet": WALLET_KEY, "monitor": MONITOR_KEY, "forged": "forged-seal"}
DEFAULT = {"amount": "10.00", "category": "GROCERIES", "merchant": "Shop"}


def payments_of(s: dict) -> list[fraud_pb2.CheckPaymentRequest]:
    raw = [{}] * s["batchSize"] if s.get("batchSize") else s.get("payments", [{}])
    return [
        fraud_pb2.CheckPaymentRequest(
            transaction_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            card_last4="4242",
            amount=p.get("amount", DEFAULT["amount"]),
            currency="EUR",
            merchant_name=p.get("merchant", DEFAULT["merchant"]),
            merchant_category=p.get("category", DEFAULT["category"]),
        )
        for p in ({**DEFAULT, **p} for p in raw)
    ]


def metadata_of(s: dict) -> tuple:
    seal = s.get("seal", "wallet")
    md = [] if seal is None else [("x-api-key", SEALS[seal])]
    if s.get("requestId"):
        md.append(("x-request-id", s["requestId"]))
    return tuple(md)


def answer(r) -> dict:
    return {
        "decision": fraud_pb2.Decision.Name(r.decision),
        "reason": r.reason,
        "riskScore": r.risk_score,
    }


def run_real(stub, s: dict) -> dict:
    """Make the call a scenario describes; return code, answers, summary and trailers."""
    method, deadline, md = s["method"], s.get("deadline", 2), metadata_of(s)
    payments = payments_of(s)
    result = {"answers": [], "summary": None, "trailers": {}}
    helpers: list = []
    try:
        wallet = (("x-api-key", WALLET_KEY),)
        helpers += [
            Watcher(stub, timeout=8, metadata=wallet) for _ in range(s.get("openWatchers", 0))
        ]
        helpers += [IdleStream(_keyed(stub)) for _ in range(s.get("openStreams", 0))]
        for h in helpers:
            if isinstance(h, IdleStream):
                assert h.started.wait(2), "setup stream did not start"

        if method == "CheckPayment":
            r, call = stub.CheckPayment.with_call(payments[0], timeout=deadline, metadata=md)
            result["answers"].append(answer(r))
            result["trailers"] = dict(call.trailing_metadata() or ())
        elif method == "GetDecision":
            tid = str(uuid.uuid4()) if s.get("unknownTransaction") else payments[0].transaction_id
            r, call = stub.GetDecision.with_call(
                fraud_pb2.GetDecisionRequest(transaction_id=tid), timeout=deadline, metadata=md
            )
            result["answers"].append(answer(r))
        elif method == "WatchRiskEvents":
            _watch(stub, s, payments, md, result)
        elif method == "CheckBatch":
            r, call = stub.CheckBatch.with_call(iter(payments), timeout=deadline, metadata=md)
            result["summary"] = {"total": r.total, "approved": r.approved, "declined": r.declined}
            result["trailers"] = dict(call.trailing_metadata() or ())
        elif method == "ScorePayments":
            _bidi(stub, s, payments, md, result)
        result["code"] = "OK"
    except grpc.RpcError as e:
        result["code"] = e.code().name
        result["trailers"] = dict(e.trailing_metadata() or ())
    finally:
        for h in helpers:
            h.close() if isinstance(h, IdleStream) else h.cancel()
    return result


def _keyed(stub):
    """IdleStream uses the stub without metadata; give it the wallet key."""

    class Keyed:
        def ScorePayments(self, requests, timeout):  # noqa: N802
            return stub.ScorePayments(
                requests, timeout=timeout, metadata=(("x-api-key", WALLET_KEY),)
            )

    return Keyed()


def _watch(stub, s, payments, md, result):
    call = stub.WatchRiskEvents(
        fraud_pb2.WatchRiskEventsRequest(min_risk_score=s.get("minRiskScore", 0)),
        timeout=s.get("deadline", 2),
        metadata=md,
    )
    call.initial_metadata()  # subscription confirmed, or the call already failed
    events, error = [], {}

    def read():
        try:
            for ev in call:
                events.append(ev)
        except grpc.RpcError as e:
            error["code"] = e.code()

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    for p in payments:
        try:  # other clients' payments may fail (TEST_ERROR, bad amount): nothing is published
            stub.CheckPayment(p, timeout=2, metadata=(("x-api-key", WALLET_KEY),))
        except grpc.RpcError:
            pass
    if s.get("clientAction") == "cancel":
        call.cancel()
    reader.join(s.get("deadline", 2) + 3)
    ours = {p.transaction_id: i for i, p in enumerate(payments)}
    mine = sorted(
        (e for e in events if e.transaction_id in ours), key=lambda e: ours[e.transaction_id]
    )
    result["answers"] = [{"riskScore": e.risk_score} for e in mine]
    if "code" in error:
        raise _Ended(error["code"])


def _bidi(stub, s, payments, md, result):
    hold = threading.Event()
    cancel = s.get("clientAction") == "cancel"

    def requests():
        yield from payments
        if cancel:
            hold.wait(5)

    call = stub.ScorePayments(requests(), timeout=s.get("deadline", 2), metadata=md)
    if cancel:
        threading.Timer(0.5, call.cancel).start()
    try:
        for r in call:
            result["answers"].append(answer(r))
    finally:
        hold.set()
    result["trailers"] = dict(call.trailing_metadata() or ())


class _Ended(grpc.RpcError):
    def __init__(self, code):
        self._code = code

    def code(self):
        return self._code

    def trailing_metadata(self):
        return ()


def check(result: dict, expect: dict) -> None:
    assert result["code"] == expect["code"]
    fields = (("decisions", "decision"), ("reasons", "reason"), ("riskScores", "riskScore"))
    for key, field in fields:
        if key in expect:
            assert [a[field] for a in result["answers"]] == expect[key], key
    if "summary" in expect:
        assert result["summary"] == expect["summary"]
    want = expect.get("trailerRequestId")
    if want == "absent":
        assert "x-request-id" not in result["trailers"]
    elif want == "generated":
        uuid.UUID(result["trailers"]["x-request-id"])
    elif want:
        assert result["trailers"].get("x-request-id") == want


@pytest.mark.req("NFR-10")
@pytest.mark.parametrize("scenario", NORMAL, ids=[s["id"] for s in NORMAL])
def test_scenario(raw_fraud_stub, scenario):
    check(run_real(raw_fraud_stub, scenario), scenario["expect"])


@pytest.fixture(scope="module")
def buggy_stub():
    channel = grpc.insecure_channel(BUGGY_ADDR)
    try:
        grpc.channel_ready_future(channel).result(timeout=3)
    except grpc.FutureTimeoutError:
        pytest.skip(f"fraud-buggy is not running at {BUGGY_ADDR}; start the buggy profile")
    yield FraudServiceStub(channel)
    channel.close()


@pytest.mark.req("NFR-10")
@pytest.mark.parametrize("scenario", BUGGY, ids=[s["id"] for s in BUGGY])
def test_buggy_scenario(buggy_stub, scenario):
    check(run_real(buggy_stub, scenario), scenario["expect"])


@pytest.mark.req("NFR-10")
def test_every_scenario_runs_against_service():
    assert {s["id"] for s in NORMAL} | {s["id"] for s in BUGGY} == {s["id"] for s in SCENARIOS}
    assert FRAUD_ADDR  # the normal run uses the same address as the other gRPC tests
