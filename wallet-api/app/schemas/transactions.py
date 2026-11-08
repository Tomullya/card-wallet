import uuid

from pydantic import BaseModel

from app.models import Transaction
from app.schemas.common import MoneyOut, UtcDatetime


class TransactionOut(BaseModel):
    id: uuid.UUID
    type: str
    amount: MoneyOut
    currency: str
    status: str
    decline_reason: str | None
    merchant_name: str | None
    card_last4: str | None
    created_at: UtcDatetime


def transaction_out(tx: Transaction, card_last4: str | None = None) -> TransactionOut:
    return TransactionOut(
        id=tx.id,
        type=tx.type,
        amount=tx.amount,
        currency=tx.currency,
        status=tx.status,
        decline_reason=tx.decline_reason,
        merchant_name=tx.merchant_name,
        card_last4=card_last4,
        created_at=tx.created_at,
    )
