import uuid

import grpc
import pytest
from fraudpb import fraud_pb2
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc


def request(amount="10.00", merchant="Shop", category="GROCERIES"):
    return fraud_pb2.CheckPaymentRequest(
        transaction_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        card_last4="1234",
        amount=amount,
        currency="EUR",
        merchant_name=merchant,
        merchant_category=category,
    )


@pytest.mark.req("BR-FRD-01")
def test_approve(fraud_stub):
    r = fraud_stub.CheckPayment(request(), timeout=2)
    assert r.decision == fraud_pb2.APPROVE
    assert r.reason == ""
    assert r.risk_score == 10


@pytest.mark.req("BR-FRD-01")
def test_decline_high_amount(fraud_stub):
    r = fraud_stub.CheckPayment(request(amount="5000.01"), timeout=2)
    assert r.decision == fraud_pb2.DECLINE
    assert r.reason == "HIGH_AMOUNT"
    assert r.risk_score == 90


@pytest.mark.req("BR-FRD-01")
def test_decline_gambling(fraud_stub):
    r = fraud_stub.CheckPayment(request(category="GAMBLING"), timeout=2)
    assert (r.decision, r.reason, r.risk_score) == (fraud_pb2.DECLINE, "BLOCKED_CATEGORY", 80)


@pytest.mark.req("BR-FRD-02")
def test_test_error_returns_internal(fraud_stub):
    with pytest.raises(grpc.RpcError) as exc:
        fraud_stub.CheckPayment(request(merchant="TEST_ERROR"), timeout=2)
    assert exc.value.code() == grpc.StatusCode.INTERNAL


@pytest.mark.req("BR-FRD-02")
def test_test_timeout_exceeds_2s_deadline(fraud_stub):
    with pytest.raises(grpc.RpcError) as exc:
        fraud_stub.CheckPayment(request(merchant="TEST_TIMEOUT"), timeout=2)
    assert exc.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED


@pytest.mark.req("BR-FRD-01")
@pytest.mark.parametrize("amount", ["abc", "", "NaN"])
def test_invalid_amount_invalid_argument(fraud_stub, amount):
    with pytest.raises(grpc.RpcError) as exc:
        fraud_stub.CheckPayment(request(amount=amount), timeout=2)
    assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.req("BR-FRD-03")
def test_health_serving(fraud_channel):
    stub = health_pb2_grpc.HealthStub(fraud_channel)
    r = stub.Check(health_pb2.HealthCheckRequest(service=""), timeout=2)
    assert r.status == health_pb2.HealthCheckResponse.SERVING


@pytest.mark.req("BR-FRD-03")
def test_reflection_lists_service(fraud_channel):
    stub = reflection_pb2_grpc.ServerReflectionStub(fraud_channel)
    responses = stub.ServerReflectionInfo(
        iter([reflection_pb2.ServerReflectionRequest(list_services="")]), timeout=2
    )
    names = {s.name for r in responses for s in r.list_services_response.service}
    assert "fraud.v1.FraudService" in names
