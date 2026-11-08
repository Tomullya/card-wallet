import uuid

import pytest

from tests.helpers import balance_of, funded_card, pay, register_and_login, top_up


def payment_rows(db, card_id):
    return db.execute(
        "select count(*) from transactions where card_id = %s and type = 'PAYMENT'", (card_id,)
    ).fetchone()[0]


@pytest.mark.req("BR-PAY-07")
def test_same_key_same_body_returns_same_response_no_double_charge(api, db):
    client = register_and_login(api)
    card = funded_card(api, client, "100.00")
    key = uuid.uuid4().hex
    first = pay(api, client, card, "10.00", key=key)
    second = pay(api, client, card, "10.00", key=key)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert balance_of(api, client, card["account_id"]) == "89.50"
    assert payment_rows(db, card["id"]) == 1


@pytest.mark.req("BR-PAY-07")
def test_same_key_different_body_409(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    key = uuid.uuid4().hex
    pay(api, client, card, "10.00", key=key)
    r = pay(api, client, card, "11.00", key=key)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert balance_of(api, client, card["account_id"]) == "989.50"


@pytest.mark.req("BR-PAY-07")
def test_amount_formatting_does_not_change_identity(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    key = uuid.uuid4().hex
    first = pay(api, client, card, "10.00", key=key)
    second = pay(api, client, card, "10", key=key)
    assert second.status_code == 201
    assert second.json() == first.json()


@pytest.mark.req("BR-PAY-07")
def test_declined_response_is_replayed(api):
    client = register_and_login(api)
    card = funded_card(api, client, "5.00")
    key = uuid.uuid4().hex
    first = pay(api, client, card, "10.00", key=key)
    assert first.json()["decline_reason"] == "INSUFFICIENT_FUNDS"
    top_up(api, client, card["account_id"], "100.00")
    assert pay(api, client, card, "10.00", key=key).json() == first.json()


@pytest.mark.req("BR-PAY-07")
def test_same_key_different_users_independent(api):
    alice, bob = register_and_login(api), register_and_login(api)
    alice_card, bob_card = funded_card(api, alice), funded_card(api, bob)
    key = uuid.uuid4().hex
    a = pay(api, alice, alice_card, "10.00", key=key)
    b = pay(api, bob, bob_card, "20.00", key=key)
    assert a.status_code == b.status_code == 201
    assert a.json()["transaction_id"] != b.json()["transaction_id"]
    assert balance_of(api, bob, bob_card["account_id"]) == "979.50"


@pytest.mark.req("BR-PAY-07", "BR-PAY-08")
def test_key_reusable_after_503(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    key = uuid.uuid4().hex
    assert pay(api, client, card, "10.00", merchant="TEST_ERROR", key=key).status_code == 503
    r = pay(api, client, card, "10.00", merchant="Shop", key=key)
    assert r.status_code == 201
    assert r.json()["status"] == "APPROVED"
