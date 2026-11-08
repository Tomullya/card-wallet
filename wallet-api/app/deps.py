from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ApiError
from app.models import User
from app.security import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme != "Bearer" or not token:
        raise ApiError(401, "UNAUTHORIZED", "Missing or invalid Authorization header")
    user = db.get(User, decode_access_token(token))
    if user is None:
        raise ApiError(401, "UNAUTHORIZED", "Invalid or expired token")
    return user
