"""The ISTQB trainers use the real wallet rules (NFR-12).

Reads the RULES object of site/istqb/js/wallet-rules.js and compares it with the constants
of the wallet and fraud-service code, so a trainer can never teach a number the product does
not have.
"""

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest
from app.models import CardStatus, Currency, MerchantCategory
from app.schemas.cards import CardCreate
from app.schemas.common import Amount
from app.services import money, payments
from fraud_service import rules

JS = Path(__file__).resolve().parents[2] / "site/istqb/js/wallet-rules.js"


def js_rules() -> dict:
    body = re.search(
        r"export const RULES = \{(.*?)\n\};", JS.read_text(encoding="utf-8"), re.S
    ).group(1)
    body = re.sub(r"//[^\n]*", "", body)  # comments
    body = re.sub(r"(\w+):", r'"\1":', body)  # keys
    body = re.sub(r",\s*$", "", body.strip())  # trailing comma
    return json.loads("{" + body + "}")


def field_bounds(annotated) -> dict:
    meta = {}
    for item in getattr(annotated, "__metadata__", ()):
        for m in getattr(item, "metadata", []):
            for name in ("gt", "ge", "lt", "le"):
                if hasattr(m, name):
                    meta[name] = Decimal(str(getattr(m, name)))
    return meta


@pytest.mark.req("NFR-12")
def test_fraud_threshold():
    assert Decimal(js_rules()["fraudThreshold"]) == rules.HIGH_AMOUNT_THRESHOLD


@pytest.mark.req("NFR-12")
def test_payment_amount_range():
    bounds = field_bounds(Amount)
    r = js_rules()
    assert bounds["gt"] == 0 and Decimal(r["amountMin"]) == Decimal("0.01")
    assert Decimal(r["amountMax"]) == bounds["le"]


@pytest.mark.req("NFR-12")
def test_daily_limit_range_and_default():
    field = CardCreate.model_fields["daily_limit"]
    bounds = {}
    for m in field.metadata:
        for name in ("ge", "le"):
            if hasattr(m, name):
                bounds[name] = Decimal(str(getattr(m, name)))
    r = js_rules()
    assert Decimal(r["dailyLimitMin"]) == bounds["ge"]
    assert Decimal(r["dailyLimitMax"]) == bounds["le"]
    assert Decimal(r["dailyLimitDefault"]) == field.default


@pytest.mark.req("NFR-12")
def test_commission_and_cvv_attempts():
    r = js_rules()
    assert Decimal(r["minCommission"]) == money.MIN_COMMISSION
    assert r["maxCvvAttempts"] == payments.MAX_FAILED_CVV_ATTEMPTS


@pytest.mark.req("NFR-12")
def test_enums():
    r = js_rules()
    assert r["currencies"] == [c.value for c in Currency]
    assert r["categories"] == [c.value for c in MerchantCategory]
    assert r["cardStates"] == [s.value for s in CardStatus]
