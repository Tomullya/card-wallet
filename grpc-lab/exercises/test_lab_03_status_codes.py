"""Урок 3. Статус-коды. Для каждого теста: вызови метод и проверь код ошибки.

Проверка: .venv/bin/python scripts/grpc_lab_check.py 3
"""

import grpc  # noqa: F401
import pytest
from fraudpb import fraud_pb2  # noqa: F401
from lab import WALLET, payment  # noqa: F401


def test_unknown_transaction_not_found(stub):
    # stub.GetDecision(fraud_pb2.GetDecisionRequest(transaction_id="no-such-id"),
    #                  metadata=WALLET, timeout=2)
    pytest.fail("TODO: ожидаем NOT_FOUND")


def test_text_amount_invalid_argument(stub):
    # Сумма словами: payment(amount="десять")
    pytest.fail("TODO: какой код? Подумай, кто виноват — клиент или сервер")


def test_test_error_merchant_internal(stub):
    # Специальный магазин TEST_ERROR изображает поломку на сервере.
    pytest.fail("TODO: ожидаем INTERNAL")
