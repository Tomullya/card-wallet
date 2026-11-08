#!/usr/bin/env python3
"""Create a demo client with accounts, cards and a few payments (fictional data).

Usage: python3 scripts/seed_demo.py  → prints the login and the card details.
Safe to run again: a new demo e-mail is used each time if the default one exists.
"""

import sys
import uuid

import httpx

API = "http://localhost:8000/api/v1"
PASSWORD = "Demo2026pass"


def main() -> int:
    api = httpx.Client(base_url=API, timeout=15)
    email = "anna.demo@example.com"
    if (
        api.post(
            "/auth/register", json={"email": email, "name": "Anna Demo", "password": PASSWORD}
        ).status_code
        == 409
    ):
        email = f"anna.demo.{uuid.uuid4().hex[:6]}@example.com"
        api.post(
            "/auth/register", json={"email": email, "name": "Anna Demo", "password": PASSWORD}
        ).raise_for_status()
    token = api.post("/auth/login", json={"email": email, "password": PASSWORD}).json()[
        "access_token"
    ]
    h = {"Authorization": f"Bearer {token}"}

    eur = api.post("/accounts", json={"currency": "EUR"}, headers=h).json()
    pln = api.post("/accounts", json={"currency": "PLN"}, headers=h).json()
    api.post(f"/accounts/{eur['id']}/top-up", json={"amount": "1500.00"}, headers=h)
    api.post(f"/accounts/{pln['id']}/top-up", json={"amount": "800.00"}, headers=h)
    card = api.post(
        f"/accounts/{eur['id']}/cards", json={"daily_limit": "500.00"}, headers=h
    ).json()
    pln_card = api.post(f"/accounts/{pln['id']}/cards", json={}, headers=h).json()

    def pay(c, amount, merchant, category, cvv=None):
        api.post(
            "/payments",
            headers={**h, "Idempotency-Key": uuid.uuid4().hex},
            json={
                "card_id": c["id"],
                "cvv": cvv or c["cvv"],
                "amount": amount,
                "merchant_name": merchant,
                "merchant_category": category,
            },
        )

    pay(card, "4.80", "Corner Bakery", "GROCERIES")
    pay(card, "129.99", "Electro World", "ELECTRONICS")
    pay(card, "25.00", "Lucky Casino", "GAMBLING")  # declined by anti-fraud
    pay(pln_card, "56.20", "Pizza Napoli", "RESTAURANTS")

    print(f"Login:    {email}")
    print(f"Password: {PASSWORD}")
    print(f"EUR card: {card['pan']}  CVV {card['cvv']}  limit 500.00/day")
    print(f"PLN card: {pln_card['pan']}  CVV {pln_card['cvv']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
