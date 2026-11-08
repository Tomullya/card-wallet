"""Parallel requests must never overdraw an account or charge twice (BR-PAY-07, BR-PAY-09)."""

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from tests.conftest import WALLET_URL
from tests.helpers import balance_of, funded_card, register_and_login


def parallel_payments(client, card, bodies_and_keys):
    barrier = threading.Barrier(len(bodies_and_keys))

    def send(item):
        amount, key = item
        with httpx.Client(base_url=f"{WALLET_URL}/api/v1", timeout=15) as http:
            barrier.wait()
            return http.post(
                "/payments",
                json={
                    "card_id": card["id"],
                    "cvv": card["cvv"],
                    "amount": amount,
                    "merchant_name": "Shop",
                    "merchant_category": "GROCERIES",
                },
                headers={**client.headers, "Idempotency-Key": key},
            )

    with ThreadPoolExecutor(len(bodies_and_keys)) as pool:
        return list(pool.map(send, bodies_and_keys))


@pytest.mark.req("BR-PAY-09")
def test_parallel_payments_never_overdraw(api):
    client = register_and_login(api)
    card = funded_card(api, client, "100.00")
    responses = parallel_payments(client, card, [("60.00", uuid.uuid4().hex) for _ in range(2)])
    assert all(r.status_code == 201 for r in responses)
    results = sorted((r.json()["status"], r.json()["decline_reason"]) for r in responses)
    assert results == [("APPROVED", None), ("DECLINED", "INSUFFICIENT_FUNDS")]
    assert balance_of(api, client, card["account_id"]) == "39.40"


@pytest.mark.req("BR-PAY-07", "BR-PAY-09")
def test_parallel_same_key_charges_once(api, db):
    client = register_and_login(api)
    card = funded_card(api, client, "100.00")
    key = uuid.uuid4().hex
    responses = parallel_payments(client, card, [("10.00", key) for _ in range(5)])
    assert all(r.status_code == 201 for r in responses), [r.text for r in responses]
    assert len({r.json()["transaction_id"] for r in responses}) == 1
    rows = db.execute(
        "select count(*) from transactions where card_id = %s and type = 'PAYMENT'", (card["id"],)
    ).fetchone()[0]
    assert rows == 1
    assert balance_of(api, client, card["account_id"]) == "89.50"
