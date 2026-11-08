from decimal import Decimal

import pytest

from tests.helpers import funded_card, pay, register_and_login


@pytest.mark.req("BR-PAY-05")
def test_approved_creates_payment_and_linked_commission(api, db):
    client = register_and_login(api)
    card = funded_card(api, client)
    tx_id = pay(api, client, card, "200.00", merchant="Book Store").json()["transaction_id"]
    rows = db.execute(
        """select id::text, type, status, amount, parent_id::text, merchant_name
           from transactions where card_id = %s order by type""",
        (card["id"],),
    ).fetchall()
    assert rows == [
        (rows[0][0], "COMMISSION", "APPROVED", Decimal("2.00"), tx_id, "Book Store"),
        (tx_id, "PAYMENT", "APPROVED", Decimal("200.00"), None, "Book Store"),
    ]


@pytest.mark.req("BR-PAY-06")
def test_declined_creates_single_declined_row(api, db):
    client = register_and_login(api)
    card = funded_card(api, client, "5.00")
    pay(api, client, card, "10.00")
    rows = db.execute(
        "select type, status, decline_reason, amount from transactions where card_id = %s",
        (card["id"],),
    ).fetchall()
    assert rows == [("PAYMENT", "DECLINED", "INSUFFICIENT_FUNDS", Decimal("10.00"))]
