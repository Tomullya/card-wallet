"""gRPC server for the anti-fraud service (BR-FRD-01 … BR-FRD-03)."""

import logging
import os
import time
from concurrent import futures
from decimal import Decimal, InvalidOperation

import grpc
from fraudpb import fraud_pb2, fraud_pb2_grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from fraud_service.auth import AuthInterceptor, current_request_id
from fraud_service.rules import evaluate

logger = logging.getLogger("fraud")

# Special merchant names that simulate failures, like test cards in payment sandboxes.
TEST_TIMEOUT_MERCHANT = "TEST_TIMEOUT"
TEST_ERROR_MERCHANT = "TEST_ERROR"
TEST_TIMEOUT_SECONDS = 5


class FraudServicer(fraud_pb2_grpc.FraudServiceServicer):
    def CheckPayment(self, request, context):  # noqa: N802 (name comes from the .proto)
        if request.merchant_name == TEST_ERROR_MERCHANT:
            context.abort(grpc.StatusCode.INTERNAL, "Simulated fraud service error")
        if request.merchant_name == TEST_TIMEOUT_MERCHANT:
            time.sleep(TEST_TIMEOUT_SECONDS)

        try:
            amount = Decimal(request.amount)
            if not amount.is_finite():
                raise InvalidOperation
        except InvalidOperation:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "amount must be a decimal number")

        decision, reason, risk_score = evaluate(amount, request.merchant_category)
        logger.info(
            "transaction=%s decision=%s reason=%s request_id=%s",
            request.transaction_id,
            decision,
            reason,
            current_request_id(),
        )
        return fraud_pb2.CheckPaymentResponse(
            decision=fraud_pb2.Decision.Value(decision), reason=reason, risk_score=risk_score
        )


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
