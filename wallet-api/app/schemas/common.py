from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, field_validator

from app.services.money import to_money


def _iso_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


# Timestamps are always returned in UTC with a "Z" suffix (NFR-02).
UtcDatetime = Annotated[datetime, PlainSerializer(_iso_utc, return_type=str)]


def _reject_bool(value: object) -> object:
    if isinstance(value, bool):
        raise ValueError("Amount must be a number")
    return value


def _money_str(value: Decimal) -> str:
    return str(to_money(value))


# Money in responses: a string with exactly 2 decimals, e.g. "100.00" (NFR-01).
MoneyOut = Annotated[Decimal, PlainSerializer(_money_str, return_type=str)]

# Money in requests: > 0, <= 10000.00, at most 2 decimal places.
Amount = Annotated[
    Decimal,
    BeforeValidator(_reject_bool),
    Field(gt=0, le=Decimal("10000.00"), max_digits=12, decimal_places=2),
    PlainSerializer(_money_str, return_type=str),
]


class RequestModel(BaseModel):
    """Base for request bodies. Rejects NUL characters, which PostgreSQL cannot store."""

    @field_validator("*", mode="after")
    @classmethod
    def _reject_nul(cls, value: object) -> object:
        if isinstance(value, str) and "\x00" in value:
            raise ValueError("Text must not contain NUL characters")
        return value
