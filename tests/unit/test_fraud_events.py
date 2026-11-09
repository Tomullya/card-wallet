"""In-memory decision store (BR-FRD-06) and risk event hub (BR-FRD-07)."""

import pytest
from fraud_service.decisions import DecisionStore
from fraud_service.events import EventHub, HubFullError
from fraudpb import fraud_pb2


def response(tid: str) -> fraud_pb2.CheckPaymentResponse:
    return fraud_pb2.CheckPaymentResponse(transaction_id=tid, risk_score=10)


def event(score: int, tid: str = "t") -> fraud_pb2.RiskEvent:
    return fraud_pb2.RiskEvent(transaction_id=tid, risk_score=score)


@pytest.mark.req("BR-FRD-06")
def test_store_returns_saved_decision():
    store = DecisionStore()
    store.put(response("a"))
    assert store.get("a").transaction_id == "a"
    assert store.get("missing") is None


@pytest.mark.req("BR-FRD-06")
def test_store_evicts_oldest():
    store = DecisionStore(capacity=2)
    for tid in ("a", "b", "c"):
        store.put(response(tid))
    assert store.get("a") is None
    assert store.get("b") is not None and store.get("c") is not None


@pytest.mark.req("BR-FRD-07")
def test_hub_filters_by_score():
    hub = EventHub()
    sub = hub.subscribe(min_risk_score=50)
    hub.publish(event(10, "low"))
    hub.publish(event(90, "high"))
    assert sub.next(timeout=0.1).transaction_id == "high"
    assert sub.next(timeout=0.1) is None


@pytest.mark.req("BR-FRD-07")
def test_hub_limit():
    hub = EventHub(max_subscribers=8)
    for _ in range(8):
        hub.subscribe(min_risk_score=0)
    with pytest.raises(HubFullError):
        hub.subscribe(min_risk_score=0)


@pytest.mark.req("BR-FRD-07")
def test_unsubscribe_frees_slot():
    hub = EventHub(max_subscribers=1)
    sub = hub.subscribe(min_risk_score=0)
    hub.unsubscribe(sub)
    assert hub.subscriber_count() == 0
    hub.subscribe(min_risk_score=0)


@pytest.mark.req("BR-FRD-07")
def test_full_queue_drops_event():
    hub = EventHub(queue_size=1)
    sub = hub.subscribe(min_risk_score=0)
    hub.publish(event(10, "first"))
    hub.publish(event(10, "second"))
    assert sub.next(timeout=0.1).transaction_id == "first"
    assert sub.next(timeout=0.1) is None
