from decimal import Decimal

import pytest
from app.services.money import calculate_commission, to_money


@pytest.mark.req("BR-PAY-03")
@pytest.mark.parametrize(
    "amount, expected",
    [
        ("10.00", "0.50"),
        ("50.00", "0.50"),
        ("100.00", "1.00"),
        ("123.45", "1.23"),
        ("0.01", "0.50"),
        ("150.50", "1.51"),  # 1.505 rounds half-up to 1.51
        ("10000.00", "100.00"),
    ],
)
def test_calculate_commission(amount, expected):
    assert calculate_commission(Decimal(amount)) == Decimal(expected)


@pytest.mark.req("NFR-01")
@pytest.mark.parametrize("value, expected", [("0.005", "0.01"), ("0.004", "0.00"), (5, "5.00")])
def test_to_money_rounds_half_up(value, expected):
    result = to_money(value)
    assert result == Decimal(expected)
    assert str(result) == expected
