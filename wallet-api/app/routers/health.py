from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.db import engine
from app.fraud_client import FraudClient, get_fraud_client

router = APIRouter(tags=["health"])


def _database_status() -> str:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


@router.get("/health")
def health(fraud: FraudClient = Depends(get_fraud_client)) -> dict:
    database = _database_status()
    fraud_service = "ok" if fraud.is_healthy() else "error"
    ok = database == "ok" and fraud_service == "ok"
    return {
        "status": "ok" if ok else "degraded",
        "database": database,
        "fraud_service": fraud_service,
    }
