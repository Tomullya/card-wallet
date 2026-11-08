"""gRPC client for the anti-fraud service (BR-FRD, BR-PAY-08)."""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache

import grpc
from fraudpb import fraud_pb2, fraud_pb2_grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from app.config import get_settings


@dataclass(frozen=True)
class FraudDecision:
    approved: bool
    reason: str | None
    risk_score: int


class FraudUnavailableError(Exception):
    """The fraud service timed out or returned an error."""


class FraudClient:
    def __init__(self, address: str, timeout_seconds: float):
        self._channel = grpc.insecure_channel(address)
        self._stub = fraud_pb2_grpc.FraudServiceStub(self._channel)
        self._health = health_pb2_grpc.HealthStub(self._channel)
        self._timeout = timeout_seconds

    def check_payment(
        self,
        *,
        transaction_id: uuid.UUID,
        user_id: uuid.UUID,
        card_last4: str,
        amount: Decimal,
        currency: str,
        merchant_name: str,
        merchant_category: str,
    ) -> FraudDecision:
        request = fraud_pb2.CheckPaymentRequest(
            transaction_id=str(transaction_id),
            user_id=str(user_id),
            card_last4=card_last4,
            amount=str(amount),
            currency=currency,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
        )
        try:
            response = self._stub.CheckPayment(request, timeout=self._timeout)
        except grpc.RpcError as exc:
            raise FraudUnavailableError(str(exc.code())) from exc
        return FraudDecision(
            approved=response.decision == fraud_pb2.APPROVE,
            reason=response.reason or None,
            risk_score=response.risk_score,
        )

    def is_healthy(self) -> bool:
        try:
            response = self._health.Check(health_pb2.HealthCheckRequest(service=""), timeout=1)
        except grpc.RpcError:
            return False
        return response.status == health_pb2.HealthCheckResponse.SERVING


@lru_cache
def get_fraud_client() -> FraudClient:
    settings = get_settings()
    return FraudClient(settings.fraud_address, settings.fraud_timeout_seconds)
