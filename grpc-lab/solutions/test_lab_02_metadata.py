"""Урок 2. Metadata: ключ доступа и ID запроса."""

import grpc
import pytest
from lab import MONITOR, WALLET, payment


def test_without_key_unauthenticated(stub):
    with pytest.raises(grpc.RpcError) as error:
        stub.CheckPayment(payment(), timeout=2)
    assert error.value.code() == grpc.StatusCode.UNAUTHENTICATED


def test_monitor_key_may_not_pay(stub):
    with pytest.raises(grpc.RpcError) as error:
        stub.CheckPayment(payment(), metadata=MONITOR, timeout=2)
    assert error.value.code() == grpc.StatusCode.PERMISSION_DENIED


def test_request_id_comes_back_in_trailers(stub):
    metadata = WALLET + (("x-request-id", "my-test-1"),)
    _, call = stub.CheckPayment.with_call(payment(), metadata=metadata, timeout=2)
    assert dict(call.trailing_metadata())["x-request-id"] == "my-test-1"
