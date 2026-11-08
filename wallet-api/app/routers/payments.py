from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.fraud_client import FraudClient, get_fraud_client
from app.models import User
from app.schemas.payments import PaymentOut, PaymentRequest
from app.services.payments import process_payment

router = APIRouter(tags=["payments"])

IdempotencyKeyHeader = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=64)]


@router.post("/payments", status_code=201, response_model=PaymentOut)
def create_payment(
    req: PaymentRequest,
    idempotency_key: IdempotencyKeyHeader,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    fraud: FraudClient = Depends(get_fraud_client),
) -> PaymentOut:
    return process_payment(db, user, req, fraud)
