import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import Account, Transaction, TxStatus, TxType, User
from app.schemas.accounts import AccountCreate, AccountOut, TopUpOut, TopUpRequest
from app.schemas.transactions import transaction_out
from app.services.money import to_money
from app.services.ownership import get_owned_account

router = APIRouter(tags=["accounts"])


@router.post("/accounts", status_code=201, response_model=AccountOut)
def open_account(
    req: AccountCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Account:
    account = Account(user_id=user.id, currency=req.currency, balance=to_money(0))
    db.add(account)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "ACCOUNT_ALREADY_EXISTS", f"You already have a {req.currency} account"
        ) from exc
    return account


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[Account]:
    query = select(Account).where(Account.user_id == user.id).order_by(Account.created_at)
    return list(db.scalars(query))


@router.get("/accounts/{account_id}", response_model=AccountOut)
def get_account(
    account_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Account:
    return get_owned_account(db, user, account_id)


@router.post("/accounts/{account_id}/top-up", status_code=201, response_model=TopUpOut)
def top_up(
    account_id: uuid.UUID,
    req: TopUpRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TopUpOut:
    account = get_owned_account(db, user, account_id, for_update=True)
    amount = to_money(req.amount)
    tx = Transaction(
        account_id=account.id,
        type=TxType.TOP_UP,
        amount=amount,
        currency=account.currency,
        status=TxStatus.APPROVED,
    )
    account.balance = to_money(account.balance + amount)
    db.add(tx)
    db.commit()
    return TopUpOut(transaction=transaction_out(tx), balance=account.balance)
