"""Урок 1. Обычный вызов (unary): один запрос — один ответ."""

from fraudpb import fraud_pb2
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc
from lab import WALLET, payment


def test_small_payment_approved(stub):
    answer = stub.CheckPayment(payment(), metadata=WALLET, timeout=2)
    assert answer.decision == fraud_pb2.APPROVE
    assert answer.risk_score == 10


def test_gambling_declined(stub):
    answer = stub.CheckPayment(payment(merchant_category="GAMBLING"), metadata=WALLET, timeout=2)
    assert answer.decision == fraud_pb2.DECLINE
    assert answer.reason == "BLOCKED_CATEGORY"
    assert answer.risk_score == 80


def test_answer_has_my_transaction_id(stub):
    request = payment()
    answer = stub.CheckPayment(request, metadata=WALLET, timeout=2)
    assert answer.transaction_id == request.transaction_id


def test_reflection_lists_the_service(channel):
    reflection = reflection_pb2_grpc.ServerReflectionStub(channel)
    replies = reflection.ServerReflectionInfo(
        iter([reflection_pb2.ServerReflectionRequest(list_services="")]), timeout=2
    )
    names = {s.name for r in replies for s in r.list_services_response.service}
    assert "fraud.v1.FraudService" in names
