"""A payment made through the REST API shows up in the gRPC risk stream (BR-FRD-07, BR-PAY-02)."""

import pytest
from fraudpb import fraud_pb2

from tests.grpc_helpers import Watcher
from tests.helpers import funded_card, pay, register_and_login


@pytest.mark.req("BR-FRD-06", "BR-FRD-07", "BR-PAY-02")
def test_rest_payment_appears_in_risk_stream(api, fraud_stub):
    client = register_and_login(api)
    card = funded_card(api, client)
    watcher = Watcher(fraud_stub, timeout=5)

    r = pay(api, client, card, "10.00", category="GAMBLING")
    tid = r.json()["transaction_id"]

    event = watcher.wait_for(lambda e: e.transaction_id == tid, timeout=3)
    assert event is not None
    assert (event.decision, event.reason, event.amount) == (
        fraud_pb2.DECLINE, "BLOCKED_CATEGORY", "10.00"
    )
    assert event.request_id  # the wallet sends x-request-id on every call
    found = fraud_stub.GetDecision(fraud_pb2.GetDecisionRequest(transaction_id=tid), timeout=2)
    assert found.decision == fraud_pb2.DECLINE
    watcher.cancel()
