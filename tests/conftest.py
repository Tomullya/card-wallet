import os
import sys
from pathlib import Path

import httpx
import psycopg
import pytest

ROOT = Path(__file__).resolve().parent.parent
# Unit tests import pure business logic directly from the services.
sys.path.insert(0, str(ROOT / "wallet-api"))
sys.path.insert(0, str(ROOT / "fraud-service"))

# Settings used when unit tests import wallet code directly.
# JWT_SECRET must match docker-compose.yml so tests can craft tokens.
os.environ.setdefault("JWT_SECRET", "local-dev-jwt-secret-not-for-production-0001")
os.environ.setdefault("CARD_HASH_SECRET", "local-dev-card-hash-secret-not-for-production")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://wallet:wallet@localhost:5433/wallet")
JWT_SECRET = os.environ["JWT_SECRET"]

WALLET_URL = os.getenv("WALLET_URL", "http://localhost:8000")
FRAUD_ADDR = os.getenv("FRAUD_ADDR", "localhost:50051")
DB_URL = os.getenv("DB_URL", "postgresql://wallet:wallet@localhost:5433/wallet")


@pytest.fixture(scope="session")
def api():
    """HTTP client for the Wallet REST API (black-box, against the running stack)."""
    with httpx.Client(base_url=f"{WALLET_URL}/api/v1", timeout=10) as client:
        yield client


@pytest.fixture
def db():
    """Direct database connection for SQL checks and test data setup."""
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        yield conn


@pytest.fixture(scope="session")
def fraud_channel():
    import grpc

    with grpc.insecure_channel(FRAUD_ADDR) as channel:
        yield channel


@pytest.fixture(scope="session")
def fraud_stub(fraud_channel):
    from fraudpb.fraud_pb2_grpc import FraudServiceStub

    return FraudServiceStub(fraud_channel)
