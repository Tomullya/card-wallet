"""Урок 9. Охота на баги: три теста, которые зелёные на :50051 и красные на :50052."""

import grpc
import pytest
from lab import WALLET, payment


def test_unknown_key_is_unauthenticated(stub):
    with pytest.raises(grpc.RpcError) as error:
        stub.CheckPayment(payment(), metadata=(("x-api-key", "typo"),), timeout=2)
    assert error.value.code() == grpc.StatusCode.UNAUTHENTICATED


def test_bidi_stream_ends_when_i_finish(stub):
    code = None
    try:
        list(stub.ScorePayments(iter([payment(), payment()]), metadata=WALLET, timeout=3))
    except grpc.RpcError as error:
        code = error.code()
    assert code is None, f"поток не закончился: {code}"


def test_request_id_returned_on_success(stub):
    metadata = WALLET + (("x-request-id", "hunt-1"),)
    _, call = stub.CheckPayment.with_call(payment(), metadata=metadata, timeout=2)
    assert dict(call.trailing_metadata()).get("x-request-id") == "hunt-1"
