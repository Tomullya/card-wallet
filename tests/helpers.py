"""Shared test helpers: create users, accounts, cards and payments through the public API."""

import uuid
from dataclasses import dataclass

PASSWORD = "Passw0rd!"


@dataclass
class AuthedClient:
    email: str
    user_id: str
    token: str

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def register(api, email: str | None = None, name: str = "Test User", password: str = PASSWORD):
    return api.post(
        "/auth/register",
        json={"email": email or unique_email(), "name": name, "password": password},
    )


def register_and_login(api) -> AuthedClient:
    email = unique_email()
    r = register(api, email)
    assert r.status_code == 201, r.text
    login = api.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    return AuthedClient(email=email, user_id=r.json()["id"], token=login.json()["access_token"])


def create_account(api, client: AuthedClient, currency: str = "EUR") -> dict:
    r = api.post("/accounts", json={"currency": currency}, headers=client.headers)
    assert r.status_code == 201, r.text
    return r.json()


def top_up(api, client: AuthedClient, account_id: str, amount: str) -> dict:
    r = api.post(f"/accounts/{account_id}/top-up", json={"amount": amount}, headers=client.headers)
    assert r.status_code == 201, r.text
    return r.json()


def issue_card(api, client: AuthedClient, account_id: str, daily_limit: str | None = None) -> dict:
    body = {} if daily_limit is None else {"daily_limit": daily_limit}
    r = api.post(f"/accounts/{account_id}/cards", json=body, headers=client.headers)
    assert r.status_code == 201, r.text
    return r.json()


def set_card_expiry(db, card_id: str, expiry) -> None:
    db.execute("update cards set expiry_date = %s where id = %s", (expiry, card_id))


def wrong_cvv(cvv: str) -> str:
    return f"{(int(cvv) + 1) % 1000:03d}"


def pay(
    api,
    client: AuthedClient,
    card: dict,
    amount: str,
    *,
    cvv: str | None = None,
    merchant: str = "Shop",
    category: str = "GROCERIES",
    key: str | None = None,
):
    """Send a card payment. Defaults: the card's real CVV and a fresh idempotency key."""
    return api.post(
        "/payments",
        json={
            "card_id": card["id"],
            "cvv": card["cvv"] if cvv is None else cvv,
            "amount": amount,
            "merchant_name": merchant,
            "merchant_category": category,
        },
        headers={**client.headers, "Idempotency-Key": key or uuid.uuid4().hex},
    )


def funded_card(
    api, client: AuthedClient, balance: str = "1000.00", daily_limit: str | None = None
) -> dict:
    """Account with the given balance (top-ups of max 10000.00 each) and one card."""
    from decimal import Decimal

    account = create_account(api, client)
    remaining = Decimal(balance)
    while remaining > 0:
        part = min(remaining, Decimal("10000.00"))
        top_up(api, client, account["id"], str(part))
        remaining -= part
    return issue_card(api, client, account["id"], daily_limit=daily_limit)


def balance_of(api, client: AuthedClient, account_id: str) -> str:
    return api.get(f"/accounts/{account_id}", headers=client.headers).json()["balance"]
