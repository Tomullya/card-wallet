"""Урок 7. Поток в обе стороны: ScorePayments.

Проверка: .venv/bin/python scripts/grpc_lab_check.py 7
"""

import grpc  # noqa: F401
import pytest
from fraudpb import fraud_pb2  # noqa: F401
from lab import WALLET, payment  # noqa: F401


def test_answers_in_my_order(stub):
    # Три платежа, средний — GAMBLING.
    # answers = list(stub.ScorePayments(iter(requests), metadata=WALLET, timeout=3))
    # Проверь: transaction_id ответов идут в том же порядке; второй ответ — DECLINE.
    pytest.fail("TODO")


def test_bad_item_stops_the_stream(stub):
    # Платежи: нормальный, amount="abc", нормальный.
    # answers = stub.ScorePayments(...)  — без list(), читаем по одному через next(answers).
    # Первый ответ приходит; второй next() бросает ошибку INVALID_ARGUMENT,
    # в error.value.details() есть "index 1".
    pytest.fail("TODO")
