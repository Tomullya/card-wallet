import re
from datetime import date

import pytest
from app.services.card_numbers import (
    expiry_for,
    format_expiry,
    generate_cvv,
    generate_pan,
    is_expired,
    luhn_is_valid,
    mask_pan,
    pan_hash,
)


@pytest.mark.req("BR-CARD-02")
@pytest.mark.parametrize(
    "pan, valid",
    [("4000000000000002", True), ("4000000000000001", False), ("79927398713", True)],
)
def test_luhn_known_values(pan, valid):
    assert luhn_is_valid(pan) is valid


@pytest.mark.req("BR-CARD-02")
def test_generate_pan_format():
    for _ in range(1000):
        pan = generate_pan()
        assert re.fullmatch(r"400000\d{10}", pan)
        assert luhn_is_valid(pan)


@pytest.mark.req("BR-CARD-03")
def test_mask_pan():
    assert mask_pan("1234") == "**** **** **** 1234"


@pytest.mark.req("BR-CARD-02")
@pytest.mark.parametrize(
    "issued, expected",
    [
        (date(2026, 11, 8), date(2029, 11, 30)),
        (date(2027, 2, 15), date(2030, 2, 28)),
        (date(2025, 2, 28), date(2028, 2, 29)),
        (date(2026, 1, 31), date(2029, 1, 31)),
    ],
)
def test_expiry_for(issued, expected):
    assert expiry_for(issued) == expected


@pytest.mark.req("BR-CARD-02")
def test_format_expiry():
    assert format_expiry(date(2029, 11, 30)) == "11/29"
    assert format_expiry(date(2030, 2, 28)) == "02/30"


@pytest.mark.req("BR-CARD-05")
def test_is_expired():
    expiry = date(2029, 11, 30)
    assert is_expired(expiry, today=date(2029, 11, 30)) is False
    assert is_expired(expiry, today=date(2029, 12, 1)) is True


@pytest.mark.req("BR-CARD-02")
def test_generate_cvv_format():
    cvvs = {generate_cvv() for _ in range(1000)}
    assert all(re.fullmatch(r"\d{3}", c) for c in cvvs)
    assert any(c.startswith("0") for c in cvvs)  # leading zeros are allowed


@pytest.mark.req("NFR-04")
def test_pan_hash_is_sha256_hex():
    h = pan_hash("4000000000000002")
    assert re.fullmatch(r"[0-9a-f]{64}", h)
    assert "4000000000000002" not in h
