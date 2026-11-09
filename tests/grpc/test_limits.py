"""Open streams must not starve payments (BR-FRD-07, BR-FRD-09, BR-PAY-08)."""

import threading

import grpc
import pytest
from fraudpb import fraud_pb2

from tests.grpc.test_fraud_service import request
from tests.grpc_helpers import Watcher

MAX_STREAMS = 16  # concurrent CheckBatch + ScorePayments calls


class IdleStream:
    """A ScorePayments call that sent one payment, got its answer and now just stays open.

    The first answer must arrive within 2 s: a stream stuck in the server's queue is a failure.
    """

    def __init__(self, stub, timeout: float = 8):
        self._release = threading.Event()
        self.started = threading.Event()

        def payments():
            yield request()
            self._release.wait(timeout)

        self.answers = stub.ScorePayments(payments(), timeout=timeout)

        def first_answer():
            try:
                next(self.answers)
                self.started.set()
            except grpc.RpcError:
                pass

        threading.Thread(target=first_answer, daemon=True).start()

    def close(self):
        self._release.set()
        self.answers.cancel()


@pytest.mark.req("BR-FRD-09", "BR-PAY-08")
def test_payments_work_while_streams_and_watchers_are_open(fraud_stub):
    watchers, streams = [], []
    try:
        watchers = [Watcher(fraud_stub, timeout=8) for _ in range(8)]
        streams = [IdleStream(fraud_stub) for _ in range(MAX_STREAMS)]
        assert all(s.started.wait(2) for s in streams), "a stream waited in the server queue"
        answer = fraud_stub.CheckPayment(request(), timeout=2)
        assert answer.decision == fraud_pb2.APPROVE
    finally:
        for s in streams:
            s.close()
        for w in watchers:
            w.cancel()


@pytest.mark.req("BR-FRD-09")
def test_stream_over_limit_resource_exhausted(fraud_stub):
    streams = []
    try:
        streams = [IdleStream(fraud_stub) for _ in range(MAX_STREAMS)]
        assert all(s.started.wait(2) for s in streams), "a stream waited in the server queue"
        extra = fraud_stub.ScorePayments(iter([request()]), timeout=3)
        with pytest.raises(grpc.RpcError) as e:
            next(extra)
        assert e.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED
        with pytest.raises(grpc.RpcError) as batch:
            fraud_stub.CheckBatch(iter([request()]), timeout=3)
        assert batch.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED
    finally:
        for s in streams:
            s.close()
