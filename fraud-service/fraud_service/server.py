"""gRPC server for the anti-fraud service (BR-FRD-01 … BR-FRD-09)."""

import logging
import os
import time
from concurrent import futures
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import grpc
from fraudpb import fraud_pb2, fraud_pb2_grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from fraud_service.auth import AuthInterceptor, current_request_id
from fraud_service.decisions import DecisionStore
from fraud_service.events import EventHub, HubFullError
from fraud_service.rules import evaluate

logger = logging.getLogger("fraud")

# Special merchant names that simulate failures, like test cards in payment sandboxes.
TEST_TIMEOUT_MERCHANT = "TEST_TIMEOUT"
TEST_ERROR_MERCHANT = "TEST_ERROR"
TEST_TIMEOUT_SECONDS = 5


def parse_amount(request) -> Decimal:
    """The request amount as a finite Decimal; ValueError if it is not one."""
    try:
        amount = Decimal(request.amount)
    except InvalidOperation:
        raise ValueError("amount must be a decimal number") from None
    if not amount.is_finite():
        raise ValueError("amount must be a decimal number")
    return amount


class FraudServicer(fraud_pb2_grpc.FraudServiceServicer):
    def __init__(self, store: DecisionStore | None = None, hub: EventHub | None = None):
        self.store = store or DecisionStore()
        self.hub = hub or EventHub()

    def decide(self, request, context, index: int | None = None):
        """Score one payment: test merchants, rules, then store and publish the decision."""
        where = "" if index is None else f" (index {index})"
        if request.merchant_name == TEST_ERROR_MERCHANT:
            context.abort(grpc.StatusCode.INTERNAL, "Simulated fraud service error" + where)
        if request.merchant_name == TEST_TIMEOUT_MERCHANT:
            time.sleep(TEST_TIMEOUT_SECONDS)
        try:
            amount = parse_amount(request)
        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"{e}{where}")

        decision, reason, risk_score = evaluate(amount, request.merchant_category)
        request_id = current_request_id()
        logger.info(
            "transaction=%s decision=%s reason=%s request_id=%s",
            request.transaction_id,
            decision,
            reason,
            request_id,
        )
        response = fraud_pb2.CheckPaymentResponse(
            decision=fraud_pb2.Decision.Value(decision),
            reason=reason,
            risk_score=risk_score,
            transaction_id=request.transaction_id,
        )
        self.store.put(response)
        self.hub.publish(
            fraud_pb2.RiskEvent(
                transaction_id=request.transaction_id,
                user_id=request.user_id,
                decision=response.decision,
                reason=reason,
                risk_score=risk_score,
                amount=request.amount,
                currency=request.currency,
                occurred_at=datetime.now(UTC).isoformat(),
                request_id=request_id,
            )
        )
        return response

    def CheckPayment(self, request, context):  # noqa: N802 (names come from the .proto)
        return self.decide(request, context)

    def GetDecision(self, request, context):  # noqa: N802
        found = self.store.get(request.transaction_id)
        if found is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "unknown transaction_id")
        return found

    def WatchRiskEvents(self, request, context):  # noqa: N802
        if not 0 <= request.min_risk_score <= 100:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "min_risk_score must be 0-100")
        try:
            sub = self.hub.subscribe(request.min_risk_score)
        except HubFullError:
            context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                f"too many watchers (max {self.hub.max_subscribers})",
            )
        context.add_callback(lambda: self.hub.unsubscribe(sub))
        # Initial metadata tells the client the subscription is active.
        context.send_initial_metadata((("x-subscribed", "true"),))
        try:
            while context.is_active():
                event = sub.next(timeout=0.5)
                if event is not None:
                    yield event
        finally:
            self.hub.unsubscribe(sub)


def serve(port: int = 50051) -> None:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=16), interceptors=[AuthInterceptor()]
    )
    fraud_pb2_grpc.add_FraudServiceServicer_to_server(FraudServicer(), server)

    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    health_servicer.set("fraud.v1.FraudService", health_pb2.HealthCheckResponse.SERVING)

    service_names = (
        fraud_pb2.DESCRIPTOR.services_by_name["FraudService"].full_name,
        health_pb2.DESCRIPTOR.services_by_name["Health"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("Fraud service listening on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    serve(int(os.getenv("PORT", "50051")))
