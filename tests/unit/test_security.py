import uuid

import pytest
from app.errors import ApiError
from app.security import create_access_token, decode_access_token, hash_secret, verify_secret


@pytest.mark.req("BR-AUTH-05")
def test_hash_secret_is_not_plaintext_and_verifies():
    hashed = hash_secret("Passw0rd!")
    assert hashed != "Passw0rd!"
    assert hashed.startswith("$2")
    assert verify_secret("Passw0rd!", hashed)
    assert not verify_secret("wrong", hashed)


@pytest.mark.req("BR-AUTH-03")
def test_token_roundtrip():
    user_id = uuid.uuid4()
    assert decode_access_token(create_access_token(user_id)) == user_id


@pytest.mark.req("BR-AUTH-03")
def test_decode_rejects_tampered_token():
    token = create_access_token(uuid.uuid4())
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(ApiError) as exc:
        decode_access_token(tampered)
    assert exc.value.status_code == 401
    assert exc.value.code == "UNAUTHORIZED"
