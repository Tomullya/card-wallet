import pytest

from tests.helpers import create_account, register_and_login, top_up


@pytest.fixture
def account(api):
    client = register_and_login(api)
    return client, create_account(api, client)


@pytest.mark.req("BR-ACC-03")
def test_topup_increases_balance(api, account):
    client, acc = account
    body = top_up(api, client, acc["id"], "100.00")
    assert body["balance"] == "100.00"
    tx = body["transaction"]
    assert tx["type"] == "TOP_UP"
    assert tx["status"] == "APPROVED"
    assert tx["amount"] == "100.00"
    assert tx["currency"] == "EUR"
    assert api.get(f"/accounts/{acc['id']}", headers=client.headers).json()["balance"] == "100.00"


@pytest.mark.req("BR-ACC-03")
def test_topups_accumulate(api, account):
    client, acc = account
    top_up(api, client, acc["id"], "0.10")
    assert top_up(api, client, acc["id"], "0.20")["balance"] == "0.30"


@pytest.mark.req("BR-ACC-03")
@pytest.mark.parametrize("amount", ["0.01", "10000.00"])
def test_topup_boundaries_accepted(api, account, amount):
    client, acc = account
    assert top_up(api, client, acc["id"], amount)["balance"] == amount


@pytest.mark.req("BR-ACC-03")
@pytest.mark.parametrize("amount", ["0", "0.00", "-1", "10000.01", "10.555"])
def test_topup_invalid_amount_422(api, account, amount):
    client, acc = account
    r = api.post(f"/accounts/{acc['id']}/top-up", json={"amount": amount}, headers=client.headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.req("BR-ACC-03", "NFR-01")
def test_topup_float_is_exact(api, account):
    client, acc = account
    r = api.post(f"/accounts/{acc['id']}/top-up", json={"amount": 10.1}, headers=client.headers)
    assert r.status_code == 201
    assert r.json()["balance"] == "10.10"


@pytest.mark.req("BR-ACC-03")
@pytest.mark.parametrize("amount", [1e30, "abc", None, True, "NaN", "Infinity", [], {}])
def test_topup_absurd_values_422(api, account, amount):
    client, acc = account
    r = api.post(f"/accounts/{acc['id']}/top-up", json={"amount": amount}, headers=client.headers)
    assert r.status_code == 422


@pytest.mark.req("BR-ACC-03", "BR-ACC-02")
def test_topup_other_users_account_404(api, account):
    _, acc = account
    stranger = register_and_login(api)
    r = api.post(f"/accounts/{acc['id']}/top-up", json={"amount": "5"}, headers=stranger.headers)
    assert r.status_code == 404
