"""Wallet API ↔ Fraud Service over gRPC (BR-PAY-02 check 6, BR-PAY-08, BR-FRD)."""

import time

import pytest

from tests.helpers import balance_of, funded_card, pay, register_and_login


def transaction_count(db, account_id):
    return db.execute(
        "select count(*) from transactions where account_id = %s", (account_id,)
    ).fetchone()[0]


@pytest.mark.req("BR-FRD-01", "BR-PAY-02")
def test_high_amount_declined_by_fraud(api):
    client = register_and_login(api)
    card = funded_card(api, client, "20000.00", daily_limit="10000.00")
    r = pay(api, client, card, "5000.01")
    assert r.json()["status"] == "DECLINED"
    assert r.json()["decline_reason"] == "FRAUD_HIGH_AMOUNT"
    assert balance_of(api, client, card["account_id"]) == "20000.00"
    assert pay(api, client, card, "5000.00").json()["status"] == "APPROVED"


@pytest.mark.req("BR-FRD-01", "BR-PAY-02")
def test_gambling_declined(api):
    client = register_and_login(api)
    card = funded_card(api, client)
    r = pay(api, client, card, "10.00", category="GAMBLING")
    assert r.json()["decline_reason"] == "FRAUD_BLOCKED_CATEGORY"
    assert balance_of(api, client, card["account_id"]) == "1000.00"


@pytest.mark.req("BR-PAY-08", "BR-FRD-02")
def test_timeout_returns_503_and_saves_nothing(api, db):
    client = register_and_login(api)
    card = funded_card(api, client)
    before = transaction_count(db, card["account_id"])
    started = time.monotonic()
    r = pay(api, client, card, "10.00", merchant="TEST_TIMEOUT")
    assert time.monotonic() - started < 4
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "FRAUD_SERVICE_UNAVAILABLE"
    assert transaction_count(db, card["account_id"]) == before
    assert balance_of(api, client, card["account_id"]) == "1000.00"


@pytest.mark.req("BR-PAY-08", "BR-FRD-02")
def test_error_returns_503(api, db):
    client = register_and_login(api)
    card = funded_card(api, client)
    before = transaction_count(db, card["account_id"])
    r = pay(api, client, card, "10.00", merchant="TEST_ERROR")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "FRAUD_SERVICE_UNAVAILABLE"
    assert transaction_count(db, card["account_id"]) == before
