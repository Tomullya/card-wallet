import os
import sys
from pathlib import Path

import httpx
import psycopg
import pytest

ROOT = Path(__file__).resolve().parent.parent
# Unit tests import pure business logic directly from the services.
sys.path.insert(0, str(ROOT / "wallet-api"))

WALLET_URL = os.getenv("WALLET_URL", "http://localhost:8000")
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
