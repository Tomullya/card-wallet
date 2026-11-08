from fastapi import APIRouter
from sqlalchemy import text

from app.db import engine

router = APIRouter(tags=["health"])


def _database_status() -> str:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


@router.get("/health")
def health() -> dict:
    database = _database_status()
    return {"status": "ok" if database == "ok" else "degraded", "database": database}
