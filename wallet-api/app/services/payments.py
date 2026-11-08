"""Card payment processing (BR-PAY-02 … BR-PAY-08, BR-CARD-06). See docs/design §6."""

import uuid
from datetime import UTC, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import buggy
from app.errors import ApiError
from app.fraud_client import FraudClient, FraudUnavailableError
from app.models import (
    Account,
    BlockReason,
    Card,
    CardStatus,
    Transaction,
    TxStatus,
    TxType,
    User,
    utcnow,
)
from app.schemas.payments import PaymentOut, PaymentRequest
from app.security import verify_secret
from app.services import idempotency
from app.services.cards import effective_status
from app.services.money import calculate_commission, to_money
from app.services.ownership import get_owned_card

MAX_FAILED_CVV_ATTEMPTS = 3
FRAUD_REASONS = {
    "HIGH_AMOUNT": "FRAUD_HIGH_AMOUNT",
    "BLOCKED_CATEGORY": "FRAUD_BLOCKED_CATEGORY",
}


class _Declined(Exception):
    def __init__(self, reason: str):
        self.reason = reason


def _spent_today(db: Session, card: Card, now: datetime) -> Decimal:
    """Sum of approved payment amounts on this card since 00:00 UTC (BR-PAY-04)."""
    midnight = datetime.combine(now.date(), time.min, tzinfo=UTC)
    total = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.card_id == card.id,
            Transaction.type == TxType.PAYMENT,
            Transaction.status == TxStatus.APPROVED,
            Transaction.created_at >= midnight,
        )
    )
    return to_money(total)


def _register_wrong_cvv(card: Card) -> None:
    card.failed_cvv_attempts += 1
    if card.failed_cvv_attempts >= MAX_FAILED_CVV_ATTEMPTS:
        card.status = CardStatus.BLOCKED
        card.block_reason = BlockReason.TOO_MANY_FAILED_ATTEMPTS


def _run_checks(
    db: Session,
    user: User,
    account: Account,
    card: Card,
    req: PaymentRequest,
    amount: Decimal,
    commission: Decimal,
    tx_id: uuid.UUID,
    now: datetime,
    fraud: FraudClient,
) -> None:
    """Raise _Declined with the first failed check, in BR-PAY-02 order."""
    status = effective_status(card, now.date())
    if status == CardStatus.BLOCKED:
        raise _Declined("CARD_BLOCKED")
    if status == CardStatus.EXPIRED:
        raise _Declined("CARD_EXPIRED")
    if not verify_secret(req.cvv, card.cvv_hash):
        _register_wrong_cvv(card)
        raise _Declined("INVALID_CVV")
    if account.balance < amount + commission:
        raise _Declined("INSUFFICIENT_FUNDS")
    spent_after = _spent_today(db, card, now) + amount
    if spent_after > card.daily_limit:
        raise _Declined("DAILY_LIMIT_EXCEEDED")
    if buggy.enabled("BUG-02") and spent_after == card.daily_limit:
        raise _Declined("DAILY_LIMIT_EXCEEDED")  # planted: exact limit declined

    decision = fraud.check_payment(
        transaction_id=tx_id,
        user_id=user.id,
        card_last4=card.pan_last4,
        amount=amount,
        currency=account.currency,
        merchant_name=req.merchant_name,
        merchant_category=req.merchant_category,
    )
    if not decision.approved:
        raise _Declined(FRAUD_REASONS.get(decision.reason or "", "FRAUD_DECLINED"))


def process_payment(
    db: Session, user: User, req: PaymentRequest, fraud: FraudClient, idempotency_key: str
) -> tuple[int, dict]:
    """Check and charge a card payment exactly once per idempotency key.

    Returns (HTTP status, response body). Raises 503 if the fraud service is unavailable;
    in that case nothing is saved and the key can be used again.
    """
    req_hash = idempotency.request_hash(req)
    if record := idempotency.find(db, user.id, idempotency_key):
        return idempotency.replay(record, req_hash)

    card = get_owned_card(db, user, req.card_id)
    # Lock order: account, then card. Prevents double spending (BR-PAY-09).
    account = db.scalar(select(Account).where(Account.id == card.account_id).with_for_update())
    db.refresh(card, with_for_update=True)
    # A parallel request with the same key may have finished while we waited for the lock.
    if record := idempotency.find(db, user.id, idempotency_key):
        db.rollback()
        return idempotency.replay(record, req_hash)

    amount = to_money(req.amount)
    commission = calculate_commission(amount)
    if buggy.enabled("BUG-01"):
        commission = to_money(amount * Decimal("0.01"))  # planted: no 0.50 minimum
    tx_id = uuid.uuid4()
    now = utcnow()
    payment = Transaction(
        id=tx_id,
        account_id=account.id,
        card_id=card.id,
        type=TxType.PAYMENT,
        amount=amount,
        currency=account.currency,
        merchant_name=req.merchant_name,
        merchant_category=req.merchant_category,
        created_at=now,
    )

    try:
        _run_checks(db, user, account, card, req, amount, commission, tx_id, now, fraud)
    except FraudUnavailableError as exc:
        db.rollback()
        raise ApiError(
            503, "FRAUD_SERVICE_UNAVAILABLE", "Payment could not be checked, try again later"
        ) from exc
    except _Declined as declined:
        payment.status = TxStatus.DECLINED
        payment.decline_reason = declined.reason
        db.add(payment)
        return _commit(db, user, idempotency_key, req_hash, _payment_out(payment, None))

    payment.status = TxStatus.APPROVED
    db.add(payment)
    db.flush()  # the commission row refers to the payment row
    db.add(
        Transaction(
            account_id=account.id,
            card_id=card.id,
            parent_id=tx_id,
            type=TxType.COMMISSION,
            amount=commission,
            currency=account.currency,
            status=TxStatus.APPROVED,
            merchant_name=req.merchant_name,
            merchant_category=req.merchant_category,
            created_at=now,
        )
    )
    account.balance = to_money(account.balance - amount - commission)
    if not buggy.enabled("BUG-03"):  # planted: counter not reset after approval
        card.failed_cvv_attempts = 0
    return _commit(db, user, idempotency_key, req_hash, _payment_out(payment, commission))


def _commit(db: Session, user: User, key: str, req_hash: str, out: PaymentOut) -> tuple[int, dict]:
    """Save the result together with the idempotency record in one database transaction."""
    body = out.model_dump(mode="json")
    idempotency.save(db, user.id, key, req_hash, 201, body)
    try:
        db.commit()
    except IntegrityError:
        # Another request with the same key won the race: undo ours, return theirs.
        db.rollback()
        record = idempotency.find(db, user.id, key)
        if record is None:
            raise
        return idempotency.replay(record, req_hash)
    return 201, body


def _payment_out(payment: Transaction, commission: Decimal | None) -> PaymentOut:
    return PaymentOut(
        transaction_id=payment.id,
        status=payment.status,
        decline_reason=payment.decline_reason,
        amount=payment.amount,
        commission=commission,
        currency=payment.currency,
        created_at=payment.created_at,
    )
