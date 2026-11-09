"""Урок 6. Поток от клиента: CheckBatch.

Проверка: .venv/bin/python scripts/grpc_lab_check.py 6
"""

import grpc  # noqa: F401
import pytest
from lab import WALLET, payment  # noqa: F401


def test_batch_totals(stub):
    # Пачка: два обычных платежа и один на 6000.00.
    # summary = stub.CheckBatch(iter(batch), metadata=WALLET, timeout=5)
    # Проверь total, approved, declined и declined_transaction_ids.
    pytest.fail("TODO")


def test_too_big_batch_resource_exhausted(stub):
    # Лимит — 1000 платежей. Генератор на 1001: (payment() for _ in range(1001))
    pytest.fail("TODO: ожидаем RESOURCE_EXHAUSTED")
