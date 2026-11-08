import pytest

from tests.helpers import (
    create_account,
    funded_card,
    pay,
    register_and_login,
    top_up,
    wrong_cvv,
)


def statement(api, client, account_id, **params):
    return api.get(f"/accounts/{account_id}/transactions", params=params, headers=client.headers)


@pytest.mark.req("BR-STM-01")
def test_newest_first_and_fields(api):
    client = register_and_login(api)
    card = funded_card(api, client, "100.00")
    pay(api, client, card, "10.00", merchant="Cafe")
    r = statement(api, client, card["account_id"])
    assert r.status_code == 200
    items = r.json()["items"]
    assert [i["type"] for i in items][2] == "TOP_UP"
    assert {i["type"] for i in items[:2]} == {"PAYMENT", "COMMISSION"}
    payment = next(i for i in items if i["type"] == "PAYMENT")
    assert payment["card_last4"] == card["pan"][-4:]
    assert payment["merchant_name"] == "Cafe"
    assert payment["amount"] == "10.00"
    assert set(payment) == {
        "id",
        "type",
        "amount",
        "currency",
        "status",
        "decline_reason",
        "merchant_name",
        "card_last4",
        "created_at",
    }
    assert items[2]["card_last4"] is None


@pytest.mark.req("BR-STM-02")
def test_filter_by_status_and_type(api):
    client = register_and_login(api)
    card = funded_card(api, client, "100.00")
    pay(api, client, card, "10.00")
    pay(api, client, card, "10.00", cvv=wrong_cvv(card["cvv"]))
    declined = statement(api, client, card["account_id"], status="DECLINED").json()
    assert [(i["type"], i["decline_reason"]) for i in declined["items"]] == [
        ("PAYMENT", "INVALID_CVV")
    ]
    commissions = statement(api, client, card["account_id"], type="COMMISSION").json()
    assert [i["amount"] for i in commissions["items"]] == ["0.50"]
    approved_payments = statement(
        api, client, card["account_id"], status="APPROVED", type="PAYMENT"
    ).json()
    assert approved_payments["total"] == 1


@pytest.mark.req("BR-STM-02")
def test_date_filters_inclusive(api, db):
    client = register_and_login(api)
    acc = create_account(api, client)
    old = top_up(api, client, acc["id"], "1.00")["transaction"]
    top_up(api, client, acc["id"], "2.00")
    db.execute(
        "update transactions set created_at = '2026-01-15T23:59:59Z' where id = %s", (old["id"],)
    )
    r = statement(api, client, acc["id"], date_from="2026-01-15", date_to="2026-01-15").json()
    assert [i["id"] for i in r["items"]] == [old["id"]]
    assert statement(api, client, acc["id"], date_to="2026-01-14").json()["total"] == 0
    assert statement(api, client, acc["id"], date_from="2026-01-16").json()["total"] == 1


@pytest.mark.req("BR-STM-02")
@pytest.mark.parametrize(
    "params",
    [
        {"date_from": "2026-02-01", "date_to": "2026-01-01"},
        {"status": "PENDING"},
        {"type": "REFUND"},
        {"date_from": "15.01.2026"},
    ],
)
def test_invalid_filters_422(api, params):
    client = register_and_login(api)
    acc = create_account(api, client)
    r = statement(api, client, acc["id"], **params)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.req("BR-STM-03")
def test_pagination(api):
    client = register_and_login(api)
    acc = create_account(api, client)
    for i in range(25):
        top_up(api, client, acc["id"], f"{i + 1}.00")
    first = statement(api, client, acc["id"]).json()
    assert (len(first["items"]), first["total"], first["limit"], first["offset"]) == (20, 25, 20, 0)
    assert first["items"][0]["amount"] == "25.00"
    second = statement(api, client, acc["id"], offset=20).json()
    assert [i["amount"] for i in second["items"]] == ["5.00", "4.00", "3.00", "2.00", "1.00"]
    assert len(statement(api, client, acc["id"], limit=100).json()["items"]) == 25
    assert len(statement(api, client, acc["id"], limit=1).json()["items"]) == 1


@pytest.mark.req("BR-STM-03")
@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_pagination_out_of_range_422(api, params):
    client = register_and_login(api)
    acc = create_account(api, client)
    assert statement(api, client, acc["id"], **params).status_code == 422


@pytest.mark.req("BR-STM-01")
def test_other_users_statement_404(api):
    client = register_and_login(api)
    acc = create_account(api, client)
    stranger = register_and_login(api)
    r = statement(api, stranger, acc["id"])
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "Account not found"


@pytest.mark.req("BR-STM-02")
def test_max_date_to_is_not_a_server_error(api):
    """Found in final review: date_to=9999-12-31 overflowed with 500."""
    client = register_and_login(api)
    acc = create_account(api, client)
    top_up(api, client, acc["id"], "1.00")
    r = statement(api, client, acc["id"], date_to="9999-12-31")
    assert r.status_code == 200
    assert r.json()["total"] == 1


@pytest.mark.req("BR-STM-03")
@pytest.mark.parametrize("offset", [2**63, 10**20])
def test_huge_offset_422(api, offset):
    """Found in final review: offsets beyond PostgreSQL bigint crashed with 500."""
    client = register_and_login(api)
    acc = create_account(api, client)
    assert statement(api, client, acc["id"], offset=offset).status_code == 422
