"""Money helpers. Money is always Decimal with 2 places, rounded half-up (NFR-01)."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")
COMMISSION_RATE = Decimal("0.01")
MIN_COMMISSION = Decimal("0.50")


def to_money(value: Decimal | str | int) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_commission(amount: Decimal) -> Decimal:
    """1% of the amount, rounded half-up to cents, minimum 0.50 (BR-PAY-03)."""
    return max(to_money(amount * COMMISSION_RATE), MIN_COMMISSION)
