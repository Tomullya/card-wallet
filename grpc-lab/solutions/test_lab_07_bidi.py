"""Урок 7. Поток в обе стороны: ScorePayments."""

import grpc
import pytest
from fraudpb import fraud_pb2
from lab import WALLET, payment


def test_answers_in_my_order(stub):
    requests = [payment(), payment(merchant_category="GAMBLING"), payment()]
    answers = list(stub.ScorePayments(iter(requests), metadata=WALLET, timeout=3))
    assert [a.transaction_id for a in answers] == [r.transaction_id for r in requests]
    assert answers[1].decision == fraud_pb2.DECLINE


def test_bad_item_stops_the_stream(stub):
    requests = [payment(), payment(amount="abc"), payment()]
    answers = stub.ScorePayments(iter(requests), metadata=WALLET, timeout=3)
    assert next(answers).transaction_id == requests[0].transaction_id
    with pytest.raises(grpc.RpcError) as error:
        next(answers)
    assert error.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert "index 1" in error.value.details()
