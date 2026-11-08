import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from tests.conftest import JWT_SECRET
from tests.helpers import PASSWORD, register, register_and_login, unique_email


@pytest.mark.req("BR-AUTH-01", "BR-AUTH-05", "NFR-02")
def test_register_success_returns_201_without_password(api):
    local = uuid.uuid4().hex[:10]
    r = register(api, email=f"User.{local}@Example.COM", name="Anna")
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == f"user.{local}@example.com"
    assert body["name"] == "Anna"
    assert {"id", "email", "name", "created_at"} == set(body)
    assert body["created_at"].endswith("Z")


@pytest.mark.req("BR-AUTH-01")
def test_register_duplicate_email_409(api):
    email = unique_email()
    assert register(api, email).status_code == 201
    r = register(api, email.upper())
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


@pytest.mark.req("BR-AUTH-01")
@pytest.mark.parametrize(
    "field, value",
    [
        ("email", "not-an-email"),
        ("name", ""),
        ("name", "   "),
        ("name", "a" * 101),
        ("password", "short12"),  # 7 characters: one below the minimum
        ("password", "onlyletters"),
        ("password", "12345678"),
    ],
)
def test_register_validation(api, field, value):
    payload = {"email": unique_email(), "name": "Anna", "password": PASSWORD, field: value}
    r = api.post("/auth/register", json=payload)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.req("BR-AUTH-01")
def test_register_boundaries_ok(api):
    assert register(api, password="abcdefg1").status_code == 201
    assert register(api, name="a" * 100).status_code == 201


@pytest.mark.req("BR-AUTH-02")
def test_login_success_returns_token(api):
    email = unique_email()
    register(api, email)
    r = api.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert body["access_token"]


@pytest.mark.req("BR-AUTH-02")
def test_login_wrong_password_and_unknown_email_same_401(api):
    email = unique_email()
    register(api, email)
    wrong_password = api.post("/auth/login", json={"email": email, "password": "Wrong1234"})
    unknown_email = api.post("/auth/login", json={"email": unique_email(), "password": PASSWORD})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.req("BR-AUTH-02")
def test_login_email_case_and_spaces_ignored(api):
    email = unique_email()
    register(api, email)
    r = api.post("/auth/login", json={"email": f"  {email.upper()} ", "password": PASSWORD})
    assert r.status_code == 200


@pytest.mark.req("BR-AUTH-04")
def test_me_returns_current_user(api):
    client = register_and_login(api)
    r = api.get("/me", headers=client.headers)
    assert r.status_code == 200
    assert r.json()["email"] == client.email
    assert r.json()["id"] == client.user_id


OTHER_SECRET = "another-secret-that-is-at-least-32-bytes"


def _token(secret: str, user_id: str, minutes: int) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=minutes)
    return jwt.encode({"sub": user_id, "exp": exp}, secret, algorithm="HS256")


@pytest.mark.req("BR-AUTH-03")
@pytest.mark.parametrize(
    "make_header",
    [
        lambda c: {},
        lambda c: {"Authorization": "Bearer garbage"},
        lambda c: {"Authorization": f"Token {c.token}"},
        lambda c: {"Authorization": f"Bearer {_token(OTHER_SECRET, c.user_id, 10)}"},
        lambda c: {"Authorization": f"Bearer {_token(JWT_SECRET, c.user_id, -1)}"},
        lambda c: {"Authorization": f"Bearer {_token(JWT_SECRET, str(uuid.uuid4()), 10)}"},
    ],
    ids=["missing", "garbage", "wrong-scheme", "wrong-secret", "expired", "unknown-user"],
)
def test_protected_endpoint_rejects_bad_tokens(api, make_header):
    client = register_and_login(api)
    r = api.get("/me", headers=make_header(client))
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.req("BR-AUTH-02")
def test_login_with_very_long_password_401_not_500(api):
    """Found by contract tests: bcrypt rejects >72 bytes and crashed login with 500."""
    email = unique_email()
    register(api, email)
    r = api.post("/auth/login", json={"email": email, "password": "a1" * 50})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.req("BR-AUTH-01")
def test_register_password_over_72_bytes_422_not_500(api):
    """72 Cyrillic characters are 144 bytes — more than bcrypt can hash."""
    r = register(api, password="пароль1" + "я" * 65)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
