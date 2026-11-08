import uuid
from datetime import UTC, datetime, timedelta

import pytest

from tests.helpers import (
    balance_of,
    funded_card,
    pay,
    register_and_login,
    set_card_expiry,
)


@pytest.fixture
def client(api):
    return register_and_login(api)


def assert_declined(r, reason):
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "DECLINED"
    assert r.json()["decline_reason"] == reason


@pytest.mark.req("BR-PAY-03", "BR-PAY-05", "NFR-02")
def test_approved_payment_charges_amount_plus_commission(api, client):
    card = funded_card(api, client, "1000.00")
    r = pay(api, client, card, "100.00")
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "APPROVED"
    assert body["decline_reason"] is None
    assert body["amount"] == "100.00"
    assert body["commission"] == "1.00"
    assert body["currency"] == "EUR"
    assert body["created_at"].endswith("Z")
    assert balance_of(api, client, card["account_id"]) == "899.00"


@pytest.mark.req("BR-PAY-03")
def test_min_commission_applied(api, client):
    card = funded_card(api, client, "100.00")
    r = pay(api, client, card, "10.00")
    assert r.json()["commission"] == "0.50"
    assert balance_of(api, client, card["account_id"]) == "89.50"


@pytest.mark.req("BR-PAY-02")
def test_insufficient_funds_considers_commission(api, client):
    card = funded_card(api, client, "100.00")
    assert_declined(pay(api, client, card, "99.50"), "INSUFFICIENT_FUNDS")  # needs 100.50
    r = pay(api, client, card, "99.00")  # needs 99.99
    assert r.json()["status"] == "APPROVED"
    assert balance_of(api, client, card["account_id"]) == "0.01"


@pytest.mark.req("BR-PAY-02")
def test_exact_balance_allowed(api, client):
    card = funded_card(api, client, "10.50")
    assert pay(api, client, card, "10.00").json()["status"] == "APPROVED"
    assert balance_of(api, client, card["account_id"]) == "0.00"


@pytest.mark.req("BR-PAY-04")
def test_daily_limit_exact_allowed(api, client):
    card = funded_card(api, client, "1000.00", daily_limit="100.00")
    assert pay(api, client, card, "60.00").json()["status"] == "APPROVED"
    assert pay(api, client, card, "40.00").json()["status"] == "APPROVED"
    assert_declined(pay(api, client, card, "0.01"), "DAILY_LIMIT_EXCEEDED")


@pytest.mark.req("BR-PAY-04")
def test_commission_does_not_count_to_limit(api, client):
    card = funded_card(api, client, "1000.00", daily_limit="100.00")
    assert pay(api, client, card, "100.00").json()["status"] == "APPROVED"


@pytest.mark.req("BR-PAY-04")
def test_declined_payments_do_not_count_to_limit(api, client):
    card = funded_card(api, client, "1000.00", daily_limit="100.00")
    assert_declined(pay(api, client, card, "100.00", category="GAMBLING"), "FRAUD_BLOCKED_CATEGORY")
    assert pay(api, client, card, "100.00").json()["status"] == "APPROVED"


@pytest.mark.req("BR-PAY-04")
def test_yesterdays_payments_do_not_count(api, db, client):
    card = funded_card(api, client, "1000.00", daily_limit="100.00")
    assert pay(api, client, card, "100.00").json()["status"] == "APPROVED"
    db.execute(
        "update transactions set created_at = created_at - interval '1 day' where card_id = %s",
        (card["id"],),
    )
    assert pay(api, client, card, "100.00").json()["status"] == "APPROVED"


@pytest.mark.req("BR-PAY-02", "BR-CARD-04")
def test_blocked_card_declined(api, client):
    card = funded_card(api, client)
    api.post(f"/cards/{card['id']}/block", headers=client.headers)
    assert_declined(pay(api, client, card, "10.00"), "CARD_BLOCKED")


@pytest.mark.req("BR-PAY-02", "BR-CARD-05")
def test_expired_card_declined(api, db, client):
    card = funded_card(api, client)
    set_card_expiry(db, card["id"], datetime.now(UTC).date() - timedelta(days=1))
    assert_declined(pay(api, client, card, "10.00"), "CARD_EXPIRED")


@pytest.mark.req("BR-PAY-02")
def test_blocked_and_expired_card_reports_blocked(api, db, client):
    card = funded_card(api, client)
    api.post(f"/cards/{card['id']}/block", headers=client.headers)
    set_card_expiry(db, card["id"], datetime.now(UTC).date() - timedelta(days=1))
    assert_declined(pay(api, client, card, "10.00"), "CARD_BLOCKED")


@pytest.mark.req("BR-PAY-06")
def test_declined_payment_does_not_change_balance(api, client):
    card = funded_card(api, client, "50.00")
    r = pay(api, client, card, "60.00")
    assert_declined(r, "INSUFFICIENT_FUNDS")
    assert r.json()["commission"] is None
    assert balance_of(api, client, card["account_id"]) == "50.00"


@pytest.mark.req("BR-PAY-01")
@pytest.mark.parametrize(
    "field, value",
    [
        ("cvv", "12"),
        ("cvv", "1234"),
        ("cvv", "abc"),
        ("amount", "0"),
        ("amount", "10000.01"),
        ("amount", "1.001"),
        ("merchant_name", ""),
        ("merchant_name", "   "),
        ("merchant_name", "m" * 101),
        ("merchant_category", "CASINO"),
        ("card_id", "not-a-uuid"),
    ],
)
def test_payment_field_validation_422(api, client, field, value):
    card = funded_card(api, client)
    body = {
        "card_id": card["id"],
        "cvv": card["cvv"],
        "amount": "10.00",
        "merchant_name": "Shop",
        "merchant_category": "GROCERIES",
        field: value,
    }
    r = api.post("/payments", json=body, headers={**client.headers, "Idempotency-Key": "k" * 10})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.req("BR-PAY-01")
@pytest.mark.parametrize("key", [None, "k" * 7, "k" * 65])
def test_idempotency_key_validation_422(api, client, key):
    card = funded_card(api, client)
    body = {
        "card_id": card["id"],
        "cvv": card["cvv"],
        "amount": "10.00",
        "merchant_name": "Shop",
        "merchant_category": "GROCERIES",
    }
    headers = dict(client.headers)
    if key is not None:
        headers["Idempotency-Key"] = key
    r = api.post("/payments", json=body, headers=headers)
    assert r.status_code == 422


@pytest.mark.req("BR-PAY-01")
@pytest.mark.parametrize("key", ["k" * 8, "k" * 64])
def test_idempotency_key_boundaries_ok(api, client, key):
    card = funded_card(api, client)
    assert pay(api, client, card, "1.00", key=key).status_code == 201


@pytest.mark.req("BR-PAY-01")
def test_other_users_card_404(api, client):
    card = funded_card(api, client)
    stranger = register_and_login(api)
    r = pay(api, stranger, card, "10.00")
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "Card not found"
    assert balance_of(api, client, card["account_id"]) == "1000.00"


@pytest.mark.req("BR-PAY-01")
def test_unknown_card_404(api, client):
    card = funded_card(api, client)
    r = pay(api, client, {**card, "id": str(uuid.uuid4())}, "10.00")
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "Card not found"
