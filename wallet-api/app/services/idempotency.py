"""Idempotency keys for payments (BR-PAY-07)."""

import hashlib
import json
import uuid

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import IdempotencyKey

# Never part of the stored hash: the other fields are in the transactions table,
# so a hash that included the CVV would let anyone recover it with 1000 guesses.
SECRET_FIELDS = {"cvv"}


def request_hash(req: BaseModel) -> str:
    """Hash of the validated request, so "10" and "10.00" count as the same body."""
    body = req.model_dump(mode="json", exclude=SECRET_FIELDS)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def find(db: Session, user_id: uuid.UUID, key: str) -> IdempotencyKey | None:
    return db.get(IdempotencyKey, (user_id, key), populate_existing=True)


def replay(record: IdempotencyKey, req_hash: str) -> tuple[int, dict]:
    """Stored response for a repeated request, or 409 if the body is different."""
    if record.request_hash != req_hash:
        raise ApiError(
            409,
            "IDEMPOTENCY_KEY_REUSED",
            "This Idempotency-Key was already used with a different request",
        )
    return record.response_code, record.response_body


def save(db: Session, user_id: uuid.UUID, key: str, req_hash: str, code: int, body: dict) -> None:
    db.add(
        IdempotencyKey(
            user_id=user_id,
            key=key,
            request_hash=req_hash,
            response_code=code,
            response_body=body,
        )
    )
