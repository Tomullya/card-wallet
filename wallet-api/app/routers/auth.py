from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.errors import ApiError
from app.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenOut, UserOut
from app.schemas.errors import error_responses
from app.security import create_access_token, hash_secret, verify_secret

router = APIRouter(tags=["auth"])

# Used when the email is unknown, so that login takes the same time either way.
_DUMMY_HASH = hash_secret("dummy-password-1")


@router.post(
    "/auth/register", status_code=201, response_model=UserOut, responses=error_responses(409, 422)
)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> User:
    user = User(email=req.email, name=req.name, password_hash=hash_secret(req.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(409, "EMAIL_ALREADY_REGISTERED", "Email is already registered") from exc
    return user


@router.post("/auth/login", response_model=TokenOut, responses=error_responses(401, 422))
def login(req: LoginRequest, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == req.email))
    password_ok = verify_secret(req.password, user.password_hash if user else _DUMMY_HASH)
    if user is None or not password_ok:
        raise ApiError(401, "INVALID_CREDENTIALS", "Invalid email or password")
    return TokenOut(
        access_token=create_access_token(user.id),
        expires_in=get_settings().jwt_ttl_minutes * 60,
    )


@router.get("/me", response_model=UserOut, responses=error_responses(401))
def me(user: User = Depends(get_current_user)) -> User:
    return user
