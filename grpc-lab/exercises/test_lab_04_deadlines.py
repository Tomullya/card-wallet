"""Урок 4. Дедлайны и отмена.

Проверка: .venv/bin/python scripts/grpc_lab_check.py 4
"""

import grpc  # noqa: F401
import pytest
from fraudpb import fraud_pb2  # noqa: F401  (fraud_pb2.APPROVE)
from lab import WALLET, Watch, payment  # noqa: F401


def test_slow_service_deadline_exceeded(stub):
    # Магазин TEST_TIMEOUT отвечает через 5 секунд. Дай клиенту дедлайн 1 секунда (timeout=1).
    pytest.fail("TODO: ожидаем DEADLINE_EXCEEDED")


def test_cancelled_stream(stub):
    # watch = Watch(stub, seconds=5) — подписка на поток событий.
    # watch.stop() отменяет вызов со стороны клиента и возвращает итоговый код.
    pytest.fail("TODO: ожидаем CANCELLED")
