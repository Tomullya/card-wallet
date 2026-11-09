"""Bidirectional streaming ScorePayments (BR-FRD-09)."""

import threading

import grpc
import pytest
from fraudpb import fraud_pb2

from tests.grpc.test_fraud_service import request


@pytest.mark.req("BR-FRD-01", "BR-FRD-09")
def test_one_answer_per_request_in_order(fraud_stub):
    reqs = [request(), request(amount="5000.01"), request(category="GAMBLING")]
    answers = list(fraud_stub.ScorePayments(iter(reqs), timeout=3))
    assert [a.transaction_id for a in answers] == [r.transaction_id for r in reqs]
    assert [a.decision for a in answers] == [
        fraud_pb2.APPROVE, fraud_pb2.DECLINE, fraud_pb2.DECLINE
    ]


@pytest.mark.req("BR-FRD-09")
def test_answer_arrives_before_next_request(fraud_stub):
    """The first answer comes while the client still holds back the second payment."""
    first, second = request(), request()
    release = threading.Event()

    def payments():
        yield first
        release.wait(3)
        yield second

    answers = fraud_stub.ScorePayments(payments(), timeout=3)
    assert next(answers).transaction_id == first.transaction_id
    release.set()
    assert next(answers).transaction_id == second.transaction_id


@pytest.mark.req("BR-FRD-09")
def test_stream_ends_after_client_closes(fraud_stub):
    reqs = [request(), request()]
    answers, code = [], None
    try:
        answers = list(fraud_stub.ScorePayments(iter(reqs), timeout=3))
    except grpc.RpcError as e:
        code = e.code()
    assert code is None, f"stream did not end: {code}"
    assert len(answers) == 2


@pytest.mark.req("BR-FRD-09")
def test_invalid_item_ends_stream(fraud_stub):
    reqs = [request(), request(amount="abc"), request()]
    answers = fraud_stub.ScorePayments(iter(reqs), timeout=3)
    assert next(answers).transaction_id == reqs[0].transaction_id
    with pytest.raises(grpc.RpcError) as e:
        next(answers)
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert "index 1" in e.value.details()
