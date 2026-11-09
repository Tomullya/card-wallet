"""Publish / subscribe hub for live risk events (BR-FRD-07)."""

import logging
import queue
import threading

from fraudpb import fraud_pb2

logger = logging.getLogger("fraud.events")


class HubFullError(Exception):
    """All watcher slots are taken."""


class Subscription:
    def __init__(self, min_risk_score: int, queue_size: int):
        self.min_risk_score = min_risk_score
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)

    def offer(self, event: fraud_pb2.RiskEvent) -> None:
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.warning("watcher too slow, dropped event transaction=%s", event.transaction_id)

    def next(self, timeout: float) -> fraud_pb2.RiskEvent | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None


class EventHub:
    def __init__(self, max_subscribers: int = 8, queue_size: int = 1000):
        self.max_subscribers = max_subscribers
        self._queue_size = queue_size
        self._subscribers: list[Subscription] = []
        self._lock = threading.Lock()

    def subscribe(self, min_risk_score: int) -> Subscription:
        with self._lock:
            if len(self._subscribers) >= self.max_subscribers:
                raise HubFullError
            sub = Subscription(min_risk_score, self._queue_size)
            self._subscribers.append(sub)
            return sub

    def unsubscribe(self, sub: Subscription) -> None:
        with self._lock:
            if sub in self._subscribers:
                self._subscribers.remove(sub)

    def publish(self, event: fraud_pb2.RiskEvent) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for sub in subscribers:
            if event.risk_score >= sub.min_risk_score:
                sub.offer(event)

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)
