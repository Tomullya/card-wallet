"""Урок 3. Статус-коды."""

import grpc
import pytest
from fraudpb import fraud_pb2
from lab import WALLET, payment


def test_unknown_transaction_not_found(stub):
    with pytest.raises(grpc.RpcError) as error:
        stub.GetDecision(
            fraud_pb2.GetDecisionRequest(transaction_id="no-such-id"), metadata=WALLET, timeout=2
        )
    assert error.value.code() == grpc.StatusCode.NOT_FOUND


def test_text_amount_invalid_argument(stub):
    with pytest.raises(grpc.RpcError) as error:
        stub.CheckPayment(payment(amount="десять"), metadata=WALLET, timeout=2)
    assert error.value.code() == grpc.StatusCode.INVALID_ARGUMENT


def test_test_error_merchant_internal(stub):
    with pytest.raises(grpc.RpcError) as error:
        stub.CheckPayment(payment(merchant_name="TEST_ERROR"), metadata=WALLET, timeout=2)
    assert error.value.code() == grpc.StatusCode.INTERNAL
