from decimal import Decimal

import pytest

from tests.helpers import create_account, register_and_login, top_up


@pytest.mark.req("BR-ACC-03", "NFR-01")
def test_topup_saves_transaction_row(api, db):
    client = register_and_login(api)
    acc = create_account(api, client, "PLN")
    top_up(api, client, acc["id"], "25.50")
    rows = db.execute(
        "select type, status, amount, currency from transactions where account_id = %s",
        (acc["id"],),
    ).fetchall()
    assert rows == [("TOP_UP", "APPROVED", Decimal("25.50"), "PLN")]
    balance = db.execute("select balance from accounts where id = %s", (acc["id"],)).fetchone()[0]
    assert balance == Decimal("25.50")
