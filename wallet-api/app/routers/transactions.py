import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import TxStatus, TxType, User
from app.schemas.errors import error_responses
from app.schemas.transactions import TransactionOut, transaction_out
from app.services.ownership import get_owned_account
from app.services.statement import StatementFilters, list_transactions

router = APIRouter(tags=["transactions"])


class StatementOut(BaseModel):
    items: list[TransactionOut]
    total: int
    limit: int
    offset: int


@router.get(
    "/accounts/{account_id}/transactions",
    response_model=StatementOut,
    responses=error_responses(401, 404, 422),
)
def get_statement(
    account_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    status: TxStatus | None = None,
    type: TxType | None = None,  # noqa: A002 (public query parameter name)
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=2**63 - 1)] = 0,  # PostgreSQL bigint
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatementOut:
    if date_from and date_to and date_from > date_to:
        raise ApiError(422, "VALIDATION_ERROR", "date_from must not be later than date_to")
    account = get_owned_account(db, user, account_id)
    filters = StatementFilters(date_from, date_to, status, type, limit, offset)
    rows, total = list_transactions(db, account, filters)
    return StatementOut(
        items=[transaction_out(tx, last4) for tx, last4 in rows],
        total=total,
        limit=limit,
        offset=offset,
    )
