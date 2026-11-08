"""Password/CVV hashing and JWT access tokens."""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import get_settings
from app.errors import ApiError

_ALGORITHM = "HS256"


def hash_secret(value: str) -> str:
    return bcrypt.hashpw(value.encode(), bcrypt.gensalt()).decode()


def verify_secret(value: str, hashed: str) -> bool:
    return bcrypt.checkpw(value.encode(), hashed.encode())


def create_access_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    exp = datetime.now(UTC) + timedelta(minutes=settings.jwt_ttl_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID:
    try:
        claims = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
        return uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise ApiError(401, "UNAUTHORIZED", "Invalid or expired token") from exc
