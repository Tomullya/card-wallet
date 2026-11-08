import pytest

from tests.helpers import funded_card, pay, register_and_login, top_up, wrong_cvv


@pytest.mark.req("BR-STM-04")
def test_balance_equals_sum_of_approved_transactions(api, db):
    client = register_and_login(api)
    card = funded_card(api, client, "500.00", daily_limit="300.00")
    pay(api, client, card, "123.45")  # approved
    pay(api, client, card, "10.00", cvv=wrong_cvv(card["cvv"]))  # declined: CVV
    pay(api, client, card, "250.00")  # declined: daily limit
    pay(api, client, card, "20.00", category="GAMBLING")  # declined: fraud
    top_up(api, client, card["account_id"], "0.55")
    pay(api, client, card, "0.01")  # approved, min commission

    balance, expected = db.execute(
        """select a.balance,
                  coalesce(sum(case when t.type = 'TOP_UP' then t.amount else -t.amount end), 0)
           from accounts a
           left join transactions t on t.account_id = a.id and t.status = 'APPROVED'
           where a.id = %s
           group by a.balance""",
        (card["account_id"],),
    ).fetchone()
    assert balance == expected
    assert str(balance) == "375.36"  # 500 - 123.45 - 1.23 + 0.55 - 0.01 - 0.50
