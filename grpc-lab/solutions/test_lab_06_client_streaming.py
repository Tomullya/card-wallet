"""Урок 6. Поток от клиента: CheckBatch."""

import grpc
import pytest
from lab import WALLET, payment


def test_batch_totals(stub):
    batch = [payment(), payment(), payment(amount="6000.00")]
    summary = stub.CheckBatch(iter(batch), metadata=WALLET, timeout=5)
    assert (summary.total, summary.approved, summary.declined) == (3, 2, 1)
    assert list(summary.declined_transaction_ids) == [batch[2].transaction_id]


def test_too_big_batch_resource_exhausted(stub):
    batch = (payment() for _ in range(1001))
    with pytest.raises(grpc.RpcError) as error:
        stub.CheckBatch(batch, metadata=WALLET, timeout=5)
    assert error.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED
