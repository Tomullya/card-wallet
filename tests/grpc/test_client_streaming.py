"""Client streaming CheckBatch (BR-FRD-08)."""

import grpc
import pytest
from fraudpb import fraud_pb2

from tests.conftest import MONITOR_KEY
from tests.grpc.test_fraud_service import request


@pytest.mark.req("BR-FRD-01", "BR-FRD-08")
def test_batch_summary(fraud_stub):
    ok, high, gambling = request(), request(amount="5000.01"), request(category="GAMBLING")
    summary = fraud_stub.CheckBatch(iter([ok, high, gambling]), timeout=5)
    assert (summary.total, summary.approved, summary.declined) == (3, 1, 2)
    assert list(summary.declined_transaction_ids) == [high.transaction_id, gambling.transaction_id]


@pytest.mark.req("BR-FRD-08")
def test_empty_batch_invalid_argument(fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        fraud_stub.CheckBatch(iter([]), timeout=5)
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.req("BR-FRD-08")
def test_batch_over_limit_resource_exhausted(fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        fraud_stub.CheckBatch((request() for _ in range(1001)), timeout=5)
    assert e.value.code() == grpc.StatusCode.RESOURCE_EXHAUSTED


@pytest.mark.req("BR-FRD-08")
def test_batch_of_exactly_1000_allowed(fraud_stub):
    summary = fraud_stub.CheckBatch((request() for _ in range(1000)), timeout=5)
    assert summary.total == 1000


@pytest.mark.req("BR-FRD-06", "BR-FRD-08")
def test_invalid_item_rejects_whole_batch(fraud_stub):
    first, bad = request(), request(amount="abc")
    with pytest.raises(grpc.RpcError) as e:
        fraud_stub.CheckBatch(iter([first, bad, request()]), timeout=5)
    assert e.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert "index 1" in e.value.details()
    with pytest.raises(grpc.RpcError) as lookup:
        fraud_stub.GetDecision(
            fraud_pb2.GetDecisionRequest(transaction_id=first.transaction_id), timeout=2
        )
    assert lookup.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.mark.req("BR-FRD-04")
def test_monitor_key_cannot_batch(raw_fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        raw_fraud_stub.CheckBatch(
            iter([request()]), timeout=5, metadata=(("x-api-key", MONITOR_KEY),)
        )
    assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED
