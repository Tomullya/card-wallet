"""Server streaming WatchRiskEvents (BR-FRD-07) and GetDecision (BR-FRD-06)."""

import time

import grpc
import pytest
from fraudpb import fraud_pb2

from tests.conftest import MONITOR_KEY, WALLET_KEY
from tests.grpc.test_fraud_service import request
from tests.grpc_helpers import Watcher


@pytest.mark.req("BR-FRD-07")
def test_watch_receives_new_decision(fraud_stub):
    watcher = Watcher(fraud_stub, timeout=2)
    req = request(category="GAMBLING")
    answer = fraud_stub.CheckPayment(req, timeout=2)
    event = watcher.wait_for(lambda e: e.transaction_id == req.transaction_id)
    assert event is not None
    assert (event.decision, event.reason, event.risk_score) == (
        answer.decision, answer.reason, answer.risk_score
    )
    assert (event.amount, event.currency, event.user_id) == (req.amount, "EUR", req.user_id)
    assert event.occurred_at.endswith("+00:00")
    assert watcher.join() == grpc.StatusCode.DEADLINE_EXCEEDED


@pytest.mark.req("BR-FRD-07")
def test_watch_filters_by_min_score(fraud_stub):
    watcher = Watcher(fraud_stub, min_risk_score=50, timeout=2)
    try:
        low, high = request(), request(category="GAMBLING")
        fraud_stub.CheckPayment(low, timeout=2)
        fraud_stub.CheckPayment(high, timeout=2)
        assert watcher.wait_for(lambda e: e.transaction_id == high.transaction_id) is not None
        assert all(e.transaction_id != low.transaction_id for e in watcher.events)
    finally:
        watcher.cancel()


@pytest.mark.req("BR-FRD-07")
@pytest.mark.parametrize("score", [-1, 101])
def test_watch_invalid_min_score(fraud_stub, score):
    call = fraud_stub.WatchRiskEvents(
        fraud_pb2.WatchRiskEventsRequest(min_risk_score=score), timeout=2
    )
    with pytest.raises(grpc.RpcError) as e:
        next(iter(call))
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.req("BR-FRD-07")
def test_ninth_watcher_resource_exhausted(fraud_stub):
    watchers = [Watcher(fraud_stub, timeout=5) for _ in range(8)]
    try:
        ninth = fraud_stub.WatchRiskEvents(fraud_pb2.WatchRiskEventsRequest(), timeout=2)
        with pytest.raises(grpc.RpcError) as e:
            next(iter(ninth))
        assert e.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED
    finally:
        for w in watchers:
            w.cancel()


@pytest.mark.req("BR-FRD-07")
def test_cancelled_watchers_free_their_slots(fraud_stub):
    for w in [Watcher(fraud_stub, timeout=5) for _ in range(8)]:
        w.cancel()
    deadline = time.monotonic() + 5
    while True:
        fresh = [Watcher(fraud_stub, timeout=5) for _ in range(8)]
        time.sleep(0.1)  # a refused watcher ends almost at once
        refused = any(w.code == grpc.StatusCode.RESOURCE_EXHAUSTED for w in fresh)
        for w in fresh:
            w.cancel()
        if not refused:
            break
        assert time.monotonic() < deadline, "slots of cancelled watchers were not freed"
        time.sleep(0.2)


@pytest.mark.req("BR-FRD-07")
def test_cancel_gives_cancelled(fraud_stub):
    watcher = Watcher(fraud_stub, timeout=5)
    watcher.cancel()
    assert watcher.join() == grpc.StatusCode.CANCELLED


@pytest.mark.req("BR-FRD-04", "BR-FRD-06", "BR-FRD-07")
def test_monitor_key_may_watch_and_lookup(raw_fraud_stub):
    monitor = (("x-api-key", MONITOR_KEY),)
    watcher = Watcher(raw_fraud_stub, timeout=2, metadata=monitor)
    try:
        req = request()
        raw_fraud_stub.CheckPayment(req, timeout=2, metadata=(("x-api-key", WALLET_KEY),))
        assert watcher.wait_for(lambda e: e.transaction_id == req.transaction_id) is not None
        found = raw_fraud_stub.GetDecision(
            fraud_pb2.GetDecisionRequest(transaction_id=req.transaction_id),
            timeout=2,
            metadata=monitor,
        )
        assert found.transaction_id == req.transaction_id
    finally:
        watcher.cancel()


@pytest.mark.req("BR-FRD-06")
def test_get_decision_found(fraud_stub):
    req = request(amount="5000.01")
    answer = fraud_stub.CheckPayment(req, timeout=2)
    assert answer.transaction_id == req.transaction_id
    found = fraud_stub.GetDecision(
        fraud_pb2.GetDecisionRequest(transaction_id=req.transaction_id), timeout=2
    )
    assert found == answer


@pytest.mark.req("BR-FRD-06")
def test_get_decision_not_found(fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        fraud_stub.GetDecision(fraud_pb2.GetDecisionRequest(transaction_id="nope"), timeout=2)
    assert e.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.mark.req("BR-FRD-05", "BR-FRD-07")
def test_request_id_reaches_risk_event(fraud_stub):
    watcher = Watcher(fraud_stub, timeout=2)
    try:
        req = request()
        fraud_stub.CheckPayment(req, timeout=2, metadata=(("x-request-id", "rid-7"),))
        event = watcher.wait_for(lambda e: e.transaction_id == req.transaction_id)
        assert event is not None and event.request_id == "rid-7"
    finally:
        watcher.cancel()
