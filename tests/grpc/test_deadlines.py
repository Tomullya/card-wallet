"""Deadlines are set by the client (BR-FRD-02, BR-FRD-07)."""

import time

import grpc
import pytest
from fraudpb import fraud_pb2

from tests.grpc.test_fraud_service import request
from tests.grpc_helpers import Watcher


@pytest.mark.req("BR-FRD-02")
def test_short_deadline_on_test_timeout(fraud_stub):
    started = time.monotonic()
    with pytest.raises(grpc.RpcError) as e:
        fraud_stub.CheckPayment(request(merchant="TEST_TIMEOUT"), timeout=1)
    assert e.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED
    assert time.monotonic() - started < 2


@pytest.mark.req("BR-FRD-02")
def test_long_deadline_waits_for_test_timeout(fraud_stub):
    """The same slow call succeeds when the client is willing to wait longer than 5 s."""
    r = fraud_stub.CheckPayment(request(merchant="TEST_TIMEOUT"), timeout=7)
    assert r.decision == fraud_pb2.APPROVE


@pytest.mark.req("BR-FRD-07")
def test_watch_stream_ends_at_deadline(fraud_stub):
    started = time.monotonic()
    watcher = Watcher(fraud_stub, timeout=1)
    assert watcher.join() == grpc.StatusCode.DEADLINE_EXCEEDED
    assert time.monotonic() - started < 2
