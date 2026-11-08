import uuid

import pytest

from tests.helpers import create_account, register_and_login


@pytest.mark.req("BR-ACC-01")
def test_open_account_starts_at_zero(api):
    client = register_and_login(api)
    acc = create_account(api, client, "USD")
    assert acc["currency"] == "USD"
    assert acc["balance"] == "0.00"
    assert {"id", "currency", "balance", "created_at"} == set(acc)


@pytest.mark.req("BR-ACC-01")
@pytest.mark.parametrize("currency", ["GBP", "eur", "", None])
def test_unsupported_currency_422(api, currency):
    client = register_and_login(api)
    r = api.post("/accounts", json={"currency": currency}, headers=client.headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.req("BR-ACC-01")
def test_second_account_same_currency_409(api):
    client = register_and_login(api)
    create_account(api, client, "EUR")
    r = api.post("/accounts", json={"currency": "EUR"}, headers=client.headers)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ACCOUNT_ALREADY_EXISTS"


@pytest.mark.req("BR-ACC-01")
def test_accounts_in_all_currencies(api):
    client = register_and_login(api)
    for currency in ("EUR", "USD", "PLN"):
        create_account(api, client, currency)
    r = api.get("/accounts", headers=client.headers)
    assert sorted(a["currency"] for a in r.json()) == ["EUR", "PLN", "USD"]


@pytest.mark.req("BR-ACC-02")
def test_list_returns_only_own_accounts(api):
    alice, bob = register_and_login(api), register_and_login(api)
    own = create_account(api, alice)
    create_account(api, bob)
    r = api.get("/accounts", headers=alice.headers)
    assert r.status_code == 200
    assert [a["id"] for a in r.json()] == [own["id"]]


@pytest.mark.req("BR-ACC-02")
def test_get_own_account(api):
    client = register_and_login(api)
    acc = create_account(api, client)
    r = api.get(f"/accounts/{acc['id']}", headers=client.headers)
    assert r.status_code == 200
    assert r.json() == acc


@pytest.mark.req("BR-ACC-02")
def test_other_users_account_and_random_id_same_404(api):
    alice, bob = register_and_login(api), register_and_login(api)
    bobs = create_account(api, bob)
    foreign = api.get(f"/accounts/{bobs['id']}", headers=alice.headers)
    missing = api.get(f"/accounts/{uuid.uuid4()}", headers=alice.headers)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()
    assert foreign.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.req("BR-ACC-02")
def test_non_uuid_id_422(api):
    client = register_and_login(api)
    r = api.get("/accounts/not-a-uuid", headers=client.headers)
    assert r.status_code == 422


@pytest.mark.req("BR-AUTH-03")
def test_accounts_require_auth(api):
    assert api.get("/accounts").status_code == 401
