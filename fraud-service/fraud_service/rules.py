"""Anti-fraud decision rules (BR-FRD-01). Checked in order; the first match wins."""

from decimal import Decimal

HIGH_AMOUNT_THRESHOLD = Decimal("5000.00")


def evaluate(amount: Decimal, merchant_category: str) -> tuple[str, str, int]:
    """Return (decision, reason, risk_score)."""
    if amount > HIGH_AMOUNT_THRESHOLD:
        return "DECLINE", "HIGH_AMOUNT", 90
    if merchant_category == "GAMBLING":
        return "DECLINE", "BLOCKED_CATEGORY", 80
    return "APPROVE", "", 10
