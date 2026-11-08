"""Account statement with filters and pagination (BR-STM-01 … BR-STM-03)."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Account, Card, Transaction, TxStatus, TxType


@dataclass(frozen=True)
class StatementFilters:
    date_from: date | None = None
    date_to: date | None = None
    status: TxStatus | None = None
    type: TxType | None = None
    limit: int = 20
    offset: int = 0


def _start_of(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


def _filtered(query: Select, account: Account, f: StatementFilters) -> Select:
    query = query.where(Transaction.account_id == account.id)
    if f.date_from:
        query = query.where(Transaction.created_at >= _start_of(f.date_from))
    if f.date_to:  # inclusive: everything before the start of the next day
        query = query.where(Transaction.created_at < _start_of(f.date_to + timedelta(days=1)))
    if f.status:
        query = query.where(Transaction.status == f.status)
    if f.type:
        query = query.where(Transaction.type == f.type)
    return query


def list_transactions(
    db: Session, account: Account, f: StatementFilters
) -> tuple[list[tuple[Transaction, str | None]], int]:
    """Return ((transaction, card_last4) items for the page, total matching count)."""
    total = db.scalar(_filtered(select(func.count(Transaction.id)), account, f))
    page = (
        _filtered(select(Transaction, Card.pan_last4), account, f)
        .outerjoin(Card, Card.id == Transaction.card_id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(f.limit)
        .offset(f.offset)
    )
    return [(tx, last4) for tx, last4 in db.execute(page)], total
