"""Small helpers for the gRPC trainer exercises: keys, a payment builder and a stream watcher."""

import threading
import time
import uuid

import grpc
from fraudpb import fraud_pb2

# Metadata = a tuple of (key, value) pairs. Keys are always lowercase.
WALLET = (("x-api-key", "dev-wallet-key"),)
MONITOR = (("x-api-key", "dev-monitor-key"),)


def payment(**overrides) -> fraud_pb2.CheckPaymentRequest:
    """A valid 10.00 EUR grocery payment; pass fields to change, e.g. amount="6000.00"."""
    fields = {
        "transaction_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "card_last4": "4242",
        "amount": "10.00",
        "currency": "EUR",
        "merchant_name": "Shop",
        "merchant_category": "GROCERIES",
    }
    fields.update(overrides)
    return fraud_pb2.CheckPaymentRequest(**fields)


class Watch:
    """Listens to WatchRiskEvents in the background; collects events and the final status code."""

    def __init__(self, stub, metadata=WALLET, min_risk_score: int = 0, seconds: float = 3):
        self.call = stub.WatchRiskEvents(
            fraud_pb2.WatchRiskEventsRequest(min_risk_score=min_risk_score),
            metadata=metadata,
            timeout=seconds,
        )
        self.events = []
        self.code = None
        self.call.initial_metadata()  # returns once the server confirmed the subscription
        self._thread = threading.Thread(target=self._read, daemon=True)
        self._thread.start()

    def _read(self):
        try:
            for event in self.call:
                self.events.append(event)
            self.code = grpc.StatusCode.OK
        except grpc.RpcError as e:
            self.code = e.code()

    def find(self, transaction_id: str, seconds: float = 2):
        """The event of this transaction, or None if it did not arrive in time."""
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            for event in list(self.events):
                if event.transaction_id == transaction_id:
                    return event
            time.sleep(0.02)
        return None

    def stop(self):
        """Cancel the stream (the client hangs up) and wait for the final code."""
        self.call.cancel()
        self._thread.join(5)
        return self.code
