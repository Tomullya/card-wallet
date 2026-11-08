"""Card issuing and status rules (BR-CARD-01 … BR-CARD-05)."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import ApiError
from app.models import Account, BlockReason, Card, CardStatus
from app.schemas.cards import CardOut
from app.security import hash_secret
from app.services.card_numbers import (
    expiry_for,
    format_expiry,
    generate_cvv,
    generate_pan,
    is_expired,
    mask_pan,
    pan_hash,
)
from app.services.money import to_money

MAX_ACTIVE_CARDS = 3


def utc_today() -> date:
    return datetime.now(UTC).date()


def effective_status(card: Card, today: date) -> CardStatus:
    if card.status == CardStatus.BLOCKED:
        return CardStatus.BLOCKED
    if is_expired(card.expiry_date, today):
        return CardStatus.EXPIRED
    return CardStatus.ACTIVE


def card_out(card: Card, today: date | None = None) -> CardOut:
    return CardOut(
        id=card.id,
        account_id=card.account_id,
        masked_pan=mask_pan(card.pan_last4),
        expiry=format_expiry(card.expiry_date),
        status=effective_status(card, today or utc_today()),
        block_reason=card.block_reason,
        daily_limit=card.daily_limit,
    )


def issue_card(db: Session, account: Account, daily_limit: Decimal) -> tuple[Card, str, str]:
    """Create a card. The caller must hold a lock on the account row.

    Returns the card, the full PAN and the CVV (shown to the client only once).
    """
    today = utc_today()
    cards = db.scalars(select(Card).where(Card.account_id == account.id))
    active = sum(1 for c in cards if effective_status(c, today) == CardStatus.ACTIVE)
    if active >= MAX_ACTIVE_CARDS:
        raise ApiError(409, "CARD_LIMIT_REACHED", "An account can have at most 3 active cards")

    secret = get_settings().card_hash_secret
    pan = generate_pan()
    while db.scalar(select(Card.id).where(Card.pan_hash == pan_hash(pan, secret))):
        pan = generate_pan()
    cvv = generate_cvv()
    card = Card(
        account_id=account.id,
        pan_last4=pan[-4:],
        pan_hash=pan_hash(pan, secret),
        expiry_date=expiry_for(today),
        cvv_hash=hash_secret(cvv),
        status=CardStatus.ACTIVE,
        failed_cvv_attempts=0,
        daily_limit=to_money(daily_limit),
    )
    db.add(card)
    return card, pan, cvv


def block_by_client(card: Card) -> None:
    if card.status == CardStatus.BLOCKED:
        raise ApiError(409, "CARD_ALREADY_BLOCKED", "Card is already blocked")
    card.status = CardStatus.BLOCKED
    card.block_reason = BlockReason.BLOCKED_BY_CLIENT
