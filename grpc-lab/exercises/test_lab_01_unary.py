"""Урок 1. Обычный вызов (unary): один запрос — один ответ.

Проверка: .venv/bin/python scripts/grpc_lab_check.py 1
Подсказки: docs/grpc-lab/01-unary.md. Решение (после попытки!): grpc-lab/solutions/.
"""

import pytest
from fraudpb import fraud_pb2  # noqa: F401  (понадобится: fraud_pb2.APPROVE, fraud_pb2.DECLINE)
from lab import WALLET, payment  # noqa: F401


def test_small_payment_approved(stub):
    # 1. Вызови stub.CheckPayment(payment(), metadata=WALLET, timeout=2) и сохрани ответ.
    # 2. Проверь, что decision == fraud_pb2.APPROVE и risk_score == 10.
    pytest.fail("TODO: напиши вызов и две проверки")


def test_gambling_declined(stub):
    # Платёж с категорией GAMBLING: payment(merchant_category="GAMBLING").
    # Ожидание: DECLINE, причина "BLOCKED_CATEGORY", risk_score 80.
    pytest.fail("TODO: вызов и три проверки")


def test_answer_has_my_transaction_id(stub):
    # Сохрани запрос в переменную, отправь его и проверь,
    # что answer.transaction_id совпадает с request.transaction_id.
    pytest.fail("TODO")


def test_reflection_lists_the_service(channel):
    # Reflection: сервис сам рассказывает, какие у него методы.
    # from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc
    # stub = reflection_pb2_grpc.ServerReflectionStub(channel)
    # Отправь iter([reflection_pb2.ServerReflectionRequest(list_services="")]) в
    # stub.ServerReflectionInfo(..., timeout=2), собери имена сервисов из
    # r.list_services_response.service и проверь, что там есть "fraud.v1.FraudService".
    pytest.fail("TODO")
