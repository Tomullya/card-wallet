import re
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from app.services.card_numbers import expiry_for, format_expiry, luhn_is_valid

from tests.helpers import (
    create_account,
    issue_card,
    register_and_login,
    set_card_expiry,
)


@pytest.fixture
def owner(api):
    client = register_and_login(api)
    return client, create_account(api, client)


def utc_today() -> date:
    return datetime.now(UTC).date()


@pytest.mark.req("BR-CARD-02", "BR-CARD-03")
def test_issue_card_returns_full_pan_and_cvv_once(api, owner):
    client, acc = owner
    card = issue_card(api, client, acc["id"])
    assert re.fullmatch(r"400000\d{10}", card["pan"]) and luhn_is_valid(card["pan"])
    assert re.fullmatch(r"\d{3}", card["cvv"])
    assert card["status"] == "ACTIVE"
    assert card["daily_limit"] == "1000.00"
    assert card["account_id"] == acc["id"]
    assert card["expiry"] == format_expiry(expiry_for(utc_today()))

    view = api.get(f"/cards/{card['id']}", headers=client.headers).json()
    assert view["masked_pan"] == "**** **** **** " + card["pan"][-4:]
    assert "pan" not in view and "cvv" not in view
    assert view["block_reason"] is None


@pytest.mark.req("BR-CARD-02")
@pytest.mark.parametrize("limit", ["1.00", "10000.00"])
def test_daily_limit_boundaries_accepted(api, owner, limit):
    client, acc = owner
    assert issue_card(api, client, acc["id"], daily_limit=limit)["daily_limit"] == limit


@pytest.mark.req("BR-CARD-02")
@pytest.mark.parametrize("limit", ["0.99", "10000.01", "0", "-5", "abc"])
def test_daily_limit_invalid_422(api, owner, limit):
    client, acc = owner
    r = api.post(
        f"/accounts/{acc['id']}/cards", json={"daily_limit": limit}, headers=client.headers
    )
    assert r.status_code == 422


@pytest.mark.req("BR-CARD-01")
def test_fourth_active_card_409(api, owner):
    client, acc = owner
    for _ in range(3):
        issue_card(api, client, acc["id"])
    r = api.post(f"/accounts/{acc['id']}/cards", json={}, headers=client.headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CARD_LIMIT_REACHED"


@pytest.mark.req("BR-CARD-01", "BR-CARD-04")
def test_blocked_card_frees_slot(api, owner):
    client, acc = owner
    cards = [issue_card(api, client, acc["id"]) for _ in range(3)]
    api.post(f"/cards/{cards[0]['id']}/block", headers=client.headers)
    issue_card(api, client, acc["id"])


@pytest.mark.req("BR-CARD-01", "BR-CARD-05")
def test_expired_card_frees_slot_and_shows_expired(api, db, owner):
    client, acc = owner
    cards = [issue_card(api, client, acc["id"]) for _ in range(3)]
    set_card_expiry(db, cards[0]["id"], utc_today() - timedelta(days=1))
    view = api.get(f"/cards/{cards[0]['id']}", headers=client.headers).json()
    assert view["status"] == "EXPIRED"
    issue_card(api, client, acc["id"])


@pytest.mark.req("BR-CARD-05")
def test_card_valid_on_expiry_day(api, db, owner):
    client, acc = owner
    card = issue_card(api, client, acc["id"])
    set_card_expiry(db, card["id"], utc_today())
    assert api.get(f"/cards/{card['id']}", headers=client.headers).json()["status"] == "ACTIVE"


@pytest.mark.req("BR-CARD-04")
def test_block_card(api, owner):
    client, acc = owner
    card = issue_card(api, client, acc["id"])
    r = api.post(f"/cards/{card['id']}/block", headers=client.headers)
    assert r.status_code == 200
    assert r.json()["status"] == "BLOCKED"
    assert r.json()["block_reason"] == "BLOCKED_BY_CLIENT"
    again = api.post(f"/cards/{card['id']}/block", headers=client.headers)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "CARD_ALREADY_BLOCKED"


@pytest.mark.req("BR-CARD-03")
def test_list_cards_masked(api, owner):
    client, acc = owner
    issued = [issue_card(api, client, acc["id"]) for _ in range(2)]
    r = api.get(f"/accounts/{acc['id']}/cards", headers=client.headers)
    assert r.status_code == 200
    listed = r.json()
    assert {c["id"] for c in listed} == {c["id"] for c in issued}
    assert all(
        set(c)
        == {"id", "account_id", "masked_pan", "expiry", "status", "block_reason", "daily_limit"}
        for c in listed
    )


@pytest.mark.req("BR-CARD-01", "BR-CARD-03", "BR-CARD-04")
def test_other_users_card_and_account_404(api, owner):
    client, acc = owner
    card = issue_card(api, client, acc["id"])
    stranger = register_and_login(api)
    h = stranger.headers
    assert api.get(f"/cards/{card['id']}", headers=h).status_code == 404
    assert api.post(f"/cards/{card['id']}/block", headers=h).status_code == 404
    assert api.get(f"/accounts/{acc['id']}/cards", headers=h).status_code == 404
    assert api.post(f"/accounts/{acc['id']}/cards", json={}, headers=h).status_code == 404
    assert api.get(f"/cards/{uuid.uuid4()}", headers=h).status_code == 404
    # The owner's card is untouched.
    assert api.get(f"/cards/{card['id']}", headers=client.headers).json()["status"] == "ACTIVE"
