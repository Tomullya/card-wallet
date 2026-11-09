"""Урок 4. Дедлайны и отмена."""

import grpc
import pytest
from lab import WALLET, Watch, payment


def test_slow_service_deadline_exceeded(stub):
    with pytest.raises(grpc.RpcError) as error:
        stub.CheckPayment(payment(merchant_name="TEST_TIMEOUT"), metadata=WALLET, timeout=1)
    assert error.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED


def test_cancelled_stream(stub):
    watch = Watch(stub, seconds=5)
    assert watch.stop() == grpc.StatusCode.CANCELLED
