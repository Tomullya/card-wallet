from decimal import Decimal

import pytest
from fraud_service.rules import evaluate


@pytest.mark.req("BR-FRD-01")
@pytest.mark.parametrize(
    "amount, category, expected",
    [
        ("5000.00", "GROCERIES", ("APPROVE", "", 10)),
        ("5000.01", "GROCERIES", ("DECLINE", "HIGH_AMOUNT", 90)),
        ("10.00", "GAMBLING", ("DECLINE", "BLOCKED_CATEGORY", 80)),
        ("6000.00", "GAMBLING", ("DECLINE", "HIGH_AMOUNT", 90)),  # rule order
        ("10.00", "GROCERIES", ("APPROVE", "", 10)),
    ],
)
def test_evaluate(amount, category, expected):
    assert evaluate(Decimal(amount), category) == expected
