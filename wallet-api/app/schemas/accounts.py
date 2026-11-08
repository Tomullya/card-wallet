import uuid

from pydantic import BaseModel, ConfigDict

from app.models import Currency
from app.schemas.common import Amount, MoneyOut, RequestModel, UtcDatetime
from app.schemas.transactions import TransactionOut


class AccountCreate(RequestModel):
    currency: Currency


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    currency: str
    balance: MoneyOut
    created_at: UtcDatetime


class TopUpRequest(RequestModel):
    amount: Amount


class TopUpOut(BaseModel):
    transaction: TransactionOut
    balance: MoneyOut
