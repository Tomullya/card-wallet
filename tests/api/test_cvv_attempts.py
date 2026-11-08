import pytest

from tests.helpers import funded_card, pay, register_and_login, wrong_cvv


def card_view(api, client, card):
    return api.get(f"/cards/{card['id']}", headers=client.headers).json()


@pytest.mark.req("BR-CARD-06")
def test_three_wrong_cvv_blocks_card(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    bad = wrong_cvv(card["cvv"])
    for attempt in range(3):
        r = pay(api, client, card, "10.00", cvv=bad)
        assert r.json()["decline_reason"] == "INVALID_CVV", f"attempt {attempt + 1}"
    view = card_view(api, client, card)
    assert view["status"] == "BLOCKED"
    assert view["block_reason"] == "TOO_MANY_FAILED_ATTEMPTS"
    assert pay(api, client, card, "10.00").json()["decline_reason"] == "CARD_BLOCKED"


@pytest.mark.req("BR-CARD-06")
def test_two_wrong_cvv_keep_card_active(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    for _ in range(2):
        r = pay(api, client, card, "10.00", cvv=wrong_cvv(card["cvv"]))
        assert r.json()["decline_reason"] == "INVALID_CVV"
    assert card_view(api, client, card)["status"] == "ACTIVE"


@pytest.mark.req("BR-CARD-06")
def test_success_resets_counter(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    bad = wrong_cvv(card["cvv"])
    pay(api, client, card, "10.00", cvv=bad)
    pay(api, client, card, "10.00", cvv=bad)
    assert pay(api, client, card, "10.00").json()["status"] == "APPROVED"
    pay(api, client, card, "10.00", cvv=bad)
    pay(api, client, card, "10.00", cvv=bad)
    assert card_view(api, client, card)["status"] == "ACTIVE"


@pytest.mark.req("BR-CARD-06")
def test_other_declines_do_not_count(api):
    client = register_and_login(api)
    card = funded_card(api, client, "50.00")
    bad = wrong_cvv(card["cvv"])
    pay(api, client, card, "10.00", cvv=bad)
    pay(api, client, card, "10.00", cvv=bad)
    assert pay(api, client, card, "100.00").json()["decline_reason"] == "INSUFFICIENT_FUNDS"
    assert card_view(api, client, card)["status"] == "ACTIVE"
    pay(api, client, card, "10.00", cvv=bad)
    assert card_view(api, client, card)["status"] == "BLOCKED"


@pytest.mark.req("BR-CARD-06")
def test_attempts_on_blocked_card_do_not_count(api, db):
    client = register_and_login(api)
    card = funded_card(api, client)
    api.post(f"/cards/{card['id']}/block", headers=client.headers)
    r = pay(api, client, card, "10.00", cvv=wrong_cvv(card["cvv"]))
    assert r.json()["decline_reason"] == "CARD_BLOCKED"
    attempts = db.execute(
        "select failed_cvv_attempts from cards where id = %s", (card["id"],)
    ).fetchone()[0]
    assert attempts == 0
