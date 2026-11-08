import uuid
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from app.schemas.common import MoneyOut, RequestModel, _reject_bool

DailyLimit = Annotated[
    Decimal,
    BeforeValidator(_reject_bool),
    Field(ge=Decimal("1.00"), le=Decimal("10000.00"), max_digits=12, decimal_places=2),
]


class CardCreate(RequestModel):
    daily_limit: DailyLimit = Decimal("1000.00")


class CardOut(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    masked_pan: str
    expiry: str
    status: str
    block_reason: str | None
    daily_limit: MoneyOut


class IssuedCardOut(BaseModel):
    """Returned only once, at issuing: contains the full PAN and CVV."""

    id: uuid.UUID
    account_id: uuid.UUID
    pan: str
    cvv: str
    expiry: str
    status: str
    daily_limit: MoneyOut
