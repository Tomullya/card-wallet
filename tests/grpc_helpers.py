"""Helpers for gRPC tests: a background watcher of the risk event stream."""

import threading
import time

import grpc
from fraudpb import fraud_pb2


class Watcher:
    """Reads WatchRiskEvents in a background thread and keeps every event and the final code.

    The constructor returns once the server has confirmed the subscription (it sends initial
    metadata right after subscribing), so events published afterwards are not missed.
    """

    def __init__(self, stub, min_risk_score: int = 0, timeout: float = 3, metadata=None):
        self.call = stub.WatchRiskEvents(
            fraud_pb2.WatchRiskEventsRequest(min_risk_score=min_risk_score),
            timeout=timeout,
            metadata=metadata,
        )
        self.events: list = []
        self.code: grpc.StatusCode | None = None
        self.call.initial_metadata()
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()

    def _read(self) -> None:
        try:
            for event in self.call:
                self.events.append(event)
            self.code = grpc.StatusCode.OK
        except grpc.RpcError as e:
            self.code = e.code()

    def wait_for(self, predicate, timeout: float = 2):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for event in list(self.events):
                if predicate(event):
                    return event
            time.sleep(0.02)
        return None

    def cancel(self) -> None:
        self.call.cancel()

    def join(self, timeout: float = 6) -> grpc.StatusCode | None:
        self._thread.join(timeout)
        return self.code
