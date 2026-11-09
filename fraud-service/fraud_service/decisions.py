"""In-memory store of recent decisions, looked up by GetDecision (BR-FRD-06)."""

import threading
from collections import OrderedDict

from fraudpb import fraud_pb2


class DecisionStore:
    def __init__(self, capacity: int = 10_000):
        self._capacity = capacity
        self._items: OrderedDict[str, fraud_pb2.CheckPaymentResponse] = OrderedDict()
        self._lock = threading.Lock()

    def put(self, response: fraud_pb2.CheckPaymentResponse) -> None:
        with self._lock:
            self._items[response.transaction_id] = response
            self._items.move_to_end(response.transaction_id)
            while len(self._items) > self._capacity:
                self._items.popitem(last=False)

    def get(self, transaction_id: str) -> fraud_pb2.CheckPaymentResponse | None:
        with self._lock:
            return self._items.get(transaction_id)
