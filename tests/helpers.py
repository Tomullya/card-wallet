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
