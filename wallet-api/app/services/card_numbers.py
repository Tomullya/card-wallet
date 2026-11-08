"""Card number, expiry and CVV helpers (BR-CARD-02, BR-CARD-03, BR-CARD-05)."""

import calendar
import hashlib
import hmac
import secrets
from datetime import date

PAN_PREFIX = "400000"  # fictional range, not a real card issuer
PAN_LENGTH = 16
VALIDITY_YEARS = 3


def _luhn_check_digit(digits: str) -> str:
    """Check digit that makes digits + check digit pass the Luhn algorithm."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 0:  # every second digit from the right, counting the future check digit
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


def luhn_is_valid(pan: str) -> bool:
    return pan.isdigit() and len(pan) > 1 and _luhn_check_digit(pan[:-1]) == pan[-1]


def generate_pan(prefix: str = PAN_PREFIX) -> str:
    body_length = PAN_LENGTH - len(prefix) - 1
    body = prefix + "".join(str(secrets.randbelow(10)) for _ in range(body_length))
    return body + _luhn_check_digit(body)


def mask_pan(last4: str) -> str:
    return f"**** **** **** {last4}"


def expiry_for(issued: date) -> date:
    """Last day of the issue month, VALIDITY_YEARS later."""
    year = issued.year + VALIDITY_YEARS
    return date(year, issued.month, calendar.monthrange(year, issued.month)[1])


def format_expiry(expiry: date) -> str:
    return expiry.strftime("%m/%y")


def is_expired(expiry: date, today: date) -> bool:
    return today > expiry


def generate_cvv() -> str:
    return f"{secrets.randbelow(1000):03d}"


def pan_hash(pan: str, secret: str) -> str:
    """Keyed hash (HMAC-SHA256) of the PAN, used only to keep card numbers unique.

    A plain hash would be easy to reverse: prefix and last 4 digits are known,
    so only 10^6 candidates remain.
    """
    return hmac.new(secret.encode(), pan.encode(), hashlib.sha256).hexdigest()
