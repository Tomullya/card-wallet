import uuid
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models import MerchantCategory
from app.schemas.common import Amount, MoneyOut, UtcDatetime

MerchantName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class PaymentRequest(BaseModel):
    card_id: uuid.UUID
    cvv: str = Field(pattern=r"^\d{3}$")
    amount: Amount
    merchant_name: MerchantName
    merchant_category: MerchantCategory


class PaymentOut(BaseModel):
    transaction_id: uuid.UUID
    status: str
    decline_reason: str | None
    amount: MoneyOut
    commission: MoneyOut | None
    currency: str
    created_at: UtcDatetime
