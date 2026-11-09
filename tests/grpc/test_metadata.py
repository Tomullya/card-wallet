"""Metadata: API keys and roles (BR-FRD-04), request ids (BR-FRD-05)."""

import uuid

import grpc
import pytest
from fraudpb import fraud_pb2
from grpc_health.v1 import health_pb2, health_pb2_grpc

from tests.conftest import MONITOR_KEY, WALLET_KEY
from tests.grpc.test_fraud_service import request


def trailers(call) -> dict:
    return dict(call.trailing_metadata() or ())


@pytest.mark.req("BR-FRD-04")
def test_missing_key_unauthenticated(raw_fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        raw_fraud_stub.CheckPayment(request(), timeout=2)
    assert e.value.code() == grpc.StatusCode.UNAUTHENTICATED


@pytest.mark.req("BR-FRD-04")
def test_unknown_key_unauthenticated(raw_fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        raw_fraud_stub.CheckPayment(request(), timeout=2, metadata=(("x-api-key", "wrong"),))
    assert e.value.code() == grpc.StatusCode.UNAUTHENTICATED


@pytest.mark.req("BR-FRD-04")
def test_monitor_key_cannot_check_payment(raw_fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        raw_fraud_stub.CheckPayment(request(), timeout=2, metadata=(("x-api-key", MONITOR_KEY),))
    assert e.value.code() == grpc.StatusCode.PERMISSION_DENIED


@pytest.mark.req("BR-FRD-04")
def test_wallet_key_allowed(raw_fraud_stub):
    r = raw_fraud_stub.CheckPayment(request(), timeout=2, metadata=(("x-api-key", WALLET_KEY),))
    assert r.decision == fraud_pb2.APPROVE


@pytest.mark.req("BR-FRD-03", "BR-FRD-04")
def test_health_needs_no_key(raw_fraud_channel):
    stub = health_pb2_grpc.HealthStub(raw_fraud_channel)
    r = stub.Check(health_pb2.HealthCheckRequest(service=""), timeout=2)
    assert r.status == health_pb2.HealthCheckResponse.SERVING


@pytest.mark.req("BR-FRD-04")
def test_header_name_case_is_ignored(raw_fraud_stub):
    """gRPC metadata keys are lowercase on the wire; grpcio refuses uppercase keys itself."""
    with pytest.raises(Exception) as e:
        raw_fraud_stub.CheckPayment(request(), timeout=2, metadata=(("X-Api-Key", WALLET_KEY),))
    assert not (
        isinstance(e.value, grpc.RpcError) and e.value.code() == grpc.StatusCode.UNAUTHENTICATED
    ), "an uppercase key reached the server instead of being rejected by the client library"


@pytest.mark.req("BR-FRD-05")
def test_request_id_echoed_in_trailers(raw_fraud_stub):
    _, call = raw_fraud_stub.CheckPayment.with_call(
        request(), timeout=2, metadata=(("x-api-key", WALLET_KEY), ("x-request-id", "lab-123"))
    )
    assert trailers(call).get("x-request-id") == "lab-123"


@pytest.mark.req("BR-FRD-05")
def test_request_id_generated_when_absent(raw_fraud_stub):
    _, call = raw_fraud_stub.CheckPayment.with_call(
        request(), timeout=2, metadata=(("x-api-key", WALLET_KEY),)
    )
    uuid.UUID(trailers(call)["x-request-id"])


@pytest.mark.req("BR-FRD-05")
def test_request_id_on_error(raw_fraud_stub):
    with pytest.raises(grpc.RpcError) as e:
        raw_fraud_stub.CheckPayment(request(), timeout=2, metadata=(("x-request-id", "err-1"),))
    assert e.value.code() == grpc.StatusCode.UNAUTHENTICATED
    assert trailers(e.value).get("x-request-id") == "err-1"
