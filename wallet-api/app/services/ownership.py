"""Load objects that belong to the current client. Foreign or missing → the same 404."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import Account, User


def get_owned_account(
    db: Session, user: User, account_id: uuid.UUID, *, for_update: bool = False
) -> Account:
    query = select(Account).where(Account.id == account_id, Account.user_id == user.id)
    if for_update:
        query = query.with_for_update()
    account = db.scalar(query)
    if account is None:
        raise ApiError(404, "NOT_FOUND", "Account not found")
    return account
