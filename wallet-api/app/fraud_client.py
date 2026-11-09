"""gRPC client for the anti-fraud service (BR-FRD, BR-PAY-08)."""

import logging
import uuid
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache

import grpc
from fraudpb import fraud_pb2, fraud_pb2_grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from app.config import get_settings

logger = logging.getLogger("wallet.fraud")


@dataclass(frozen=True)
class FraudDecision:
    approved: bool
    reason: str | None
    risk_score: int


class FraudUnavailableError(Exception):
    """The fraud service timed out or returned an error."""


class FraudClient:
    def __init__(self, address: str, timeout_seconds: float, api_key: str):
        self._channel = grpc.insecure_channel(address)
        self._stub = fraud_pb2_grpc.FraudServiceStub(self._channel)
        self._health = health_pb2_grpc.HealthStub(self._channel)
        self._timeout = timeout_seconds
        self._api_key = api_key

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
        request_id = str(uuid.uuid4())
        metadata = (("x-api-key", self._api_key), ("x-request-id", request_id))
        logger.info("fraud check transaction=%s request_id=%s", transaction_id, request_id)
        try:
            response = self._stub.CheckPayment(request, timeout=self._timeout, metadata=metadata)
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
    return FraudClient(
        settings.fraud_address, settings.fraud_timeout_seconds, settings.fraud_api_key
    )
