"""Database tables (SQLAlchemy models). See docs/design §3."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

Money = Numeric(12, 2)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Currency(StrEnum):
    EUR = "EUR"
    USD = "USD"
    PLN = "PLN"


class CardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"  # never stored, calculated from expiry_date


class BlockReason(StrEnum):
    BLOCKED_BY_CLIENT = "BLOCKED_BY_CLIENT"
    TOO_MANY_FAILED_ATTEMPTS = "TOO_MANY_FAILED_ATTEMPTS"


class TxType(StrEnum):
    TOP_UP = "TOP_UP"
    PAYMENT = "PAYMENT"
    COMMISSION = "COMMISSION"


class TxStatus(StrEnum):
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"


class MerchantCategory(StrEnum):
    GROCERIES = "GROCERIES"
    ELECTRONICS = "ELECTRONICS"
    TRAVEL = "TRAVEL"
    RESTAURANTS = "RESTAURANTS"
    GAMBLING = "GAMBLING"
    OTHER = "OTHER"


def _enum(cls: type[StrEnum]) -> Enum:
    return Enum(cls, native_enum=False, length=32, values_callable=lambda e: [m.value for m in e])


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("user_id", "currency", name="uq_accounts_user_currency"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    currency: Mapped[Currency] = mapped_column(_enum(Currency))
    balance: Mapped[Decimal] = mapped_column(Money, default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), index=True)
    pan_last4: Mapped[str] = mapped_column(String(4))
    pan_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expiry_date: Mapped[date] = mapped_column(Date)
    cvv_hash: Mapped[str] = mapped_column(String(100))
    status: Mapped[CardStatus] = mapped_column(_enum(CardStatus), default=CardStatus.ACTIVE)
    block_reason: Mapped[BlockReason | None] = mapped_column(_enum(BlockReason), nullable=True)
    failed_cvv_attempts: Mapped[int] = mapped_column(Integer, default=0)
    daily_limit: Mapped[Decimal] = mapped_column(Money)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_account_created", "account_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"))
    card_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cards.id"), nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transactions.id"), nullable=True
    )
    type: Mapped[TxType] = mapped_column(_enum(TxType))
    amount: Mapped[Decimal] = mapped_column(Money)
    currency: Mapped[Currency] = mapped_column(_enum(Currency))
    status: Mapped[TxStatus] = mapped_column(_enum(TxStatus))
    decline_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    merchant_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    merchant_category: Mapped[MerchantCategory | None] = mapped_column(
        _enum(MerchantCategory), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response_code: Mapped[int] = mapped_column(Integer)
    response_body: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
