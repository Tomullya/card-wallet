import pytest


@pytest.mark.req("BR-ACC-01", "BR-CARD-01", "BR-PAY-07")
def test_tables_exist(db):
    names = {
        r[0]
        for r in db.execute(
            "select table_name from information_schema.tables where table_schema='public'"
        )
    }
    assert {"users", "accounts", "cards", "transactions", "idempotency_keys"} <= names


@pytest.mark.req("NFR-01")
def test_money_columns_are_numeric_12_2(db):
    rows = db.execute(
        """select table_name, column_name, numeric_precision, numeric_scale
           from information_schema.columns
           where table_schema='public' and column_name in ('balance','amount','daily_limit')"""
    ).fetchall()
    assert {(r[0], r[1]) for r in rows} == {
        ("accounts", "balance"),
        ("transactions", "amount"),
        ("cards", "daily_limit"),
    }
    assert all(r[2] == 12 and r[3] == 2 for r in rows)


@pytest.mark.req("BR-ACC-01")
def test_one_account_per_currency_constraint(db):
    rows = db.execute(
        """select pg_get_constraintdef(c.oid) from pg_constraint c
           join pg_class t on t.oid = c.conrelid
           where t.relname = 'accounts' and c.contype = 'u'"""
    ).fetchall()
    assert any("user_id, currency" in r[0] for r in rows)
