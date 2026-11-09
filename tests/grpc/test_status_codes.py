"""Where each gRPC status code of the Fraud Service is tested (see docs/grpc-lab/03).

| Code               | Test                                                              |
|--------------------|-------------------------------------------------------------------|
| OK                 | test_fraud_service.py::test_approve                               |
| INVALID_ARGUMENT   | test_fraud_service.py::test_invalid_amount_invalid_argument,      |
|                    | test_server_streaming.py::test_watch_invalid_min_score,           |
|                    | test_client_streaming.py::test_empty_batch_invalid_argument       |
| NOT_FOUND          | test_server_streaming.py::test_get_decision_not_found             |
| UNAUTHENTICATED    | test_metadata.py::test_missing_key_unauthenticated                |
| PERMISSION_DENIED  | test_metadata.py::test_monitor_key_cannot_check_payment           |
| RESOURCE_EXHAUSTED | test_client_streaming.py::test_batch_over_limit_resource_exhausted, |
|                    | test_server_streaming.py::test_ninth_watcher_resource_exhausted   |
| DEADLINE_EXCEEDED  | test_deadlines.py::test_short_deadline_on_test_timeout            |
| CANCELLED          | test_server_streaming.py::test_cancel_gives_cancelled             |
| INTERNAL           | test_fraud_service.py::test_test_error_returns_internal           |
| UNAVAILABLE        | test_status_codes.py::test_unavailable_on_wrong_port (below)      |
"""

import grpc
import pytest
from fraudpb.fraud_pb2_grpc import FraudServiceStub

from tests.grpc.test_fraud_service import request


@pytest.mark.req("BR-FRD-02")
def test_unavailable_on_wrong_port():
    with grpc.insecure_channel("localhost:59999") as channel:
        with pytest.raises(grpc.RpcError) as e:
            FraudServiceStub(channel).CheckPayment(request(), timeout=2)
    assert e.value.code() == grpc.StatusCode.UNAVAILABLE
