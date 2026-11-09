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
WALLET_KEY = os.getenv("FRAUD_API_KEY_WALLET", "dev-wallet-key")
MONITOR_KEY = os.getenv("FRAUD_API_KEY_MONITOR", "dev-monitor-key")
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
def raw_fraud_channel():
    """Channel to the Fraud Service that sends no metadata (for auth tests)."""
    import grpc

    with grpc.insecure_channel(FRAUD_ADDR) as channel:
        yield channel


@pytest.fixture(scope="session")
def fraud_channel(raw_fraud_channel):
    """Channel that adds the wallet API key to every call unless the call sends its own."""
    import grpc

    return grpc.intercept_channel(raw_fraud_channel, *_default_key_interceptors())


@pytest.fixture(scope="session")
def fraud_stub(fraud_channel):
    from fraudpb.fraud_pb2_grpc import FraudServiceStub

    return FraudServiceStub(fraud_channel)


@pytest.fixture(scope="session")
def raw_fraud_stub(raw_fraud_channel):
    from fraudpb.fraud_pb2_grpc import FraudServiceStub

    return FraudServiceStub(raw_fraud_channel)


def _default_key_interceptors():
    import collections

    import grpc

    class Details(
        collections.namedtuple(
            "Details",
            ("method", "timeout", "metadata", "credentials", "wait_for_ready", "compression"),
        ),
        grpc.ClientCallDetails,
    ):
        pass

    def with_key(details):
        metadata = list(details.metadata or ())
        if not any(k == "x-api-key" for k, _ in metadata):
            metadata.append(("x-api-key", WALLET_KEY))
        return Details(
            details.method, details.timeout, metadata, details.credentials,
            details.wait_for_ready, details.compression,
        )

    class AddKey(
        grpc.UnaryUnaryClientInterceptor,
        grpc.UnaryStreamClientInterceptor,
        grpc.StreamUnaryClientInterceptor,
        grpc.StreamStreamClientInterceptor,
    ):
        def intercept_unary_unary(self, continuation, details, request):
            return continuation(with_key(details), request)

        def intercept_unary_stream(self, continuation, details, request):
            return continuation(with_key(details), request)

        def intercept_stream_unary(self, continuation, details, requests):
            return continuation(with_key(details), requests)

        def intercept_stream_stream(self, continuation, details, requests):
            return continuation(with_key(details), requests)

    return (AddKey(),)


def pytest_collection_finish(session):
    """With REQ_REPORT=<path>, write {requirement_id: [test node ids]} for traceability."""
    report = os.getenv("REQ_REPORT")
    if not report:
        return
    import json
    from collections import defaultdict

    coverage = defaultdict(set)
    for item in session.items:
        nodeid = item.nodeid.split("[")[0]  # one entry per test, not per parameter
        for marker in item.iter_markers(name="req"):
            for req_id in marker.args:
                coverage[req_id].add(nodeid)
    with open(report, "w") as f:
        json.dump({k: sorted(v) for k, v in coverage.items()}, f, indent=1)


def requirement_labels(item) -> list[str]:
    """Requirement IDs from the test's @pytest.mark.req markers."""
    return [req_id for marker in item.iter_markers(name="req") for req_id in marker.args]


def level_of(item) -> str:
    """Test level = the folder under tests/ (unit, api, integration, grpc, db, contract)."""
    parts = item.nodeid.split("/")
    return parts[1] if len(parts) > 2 else "other"


def pytest_runtest_setup(item):
    """Show requirement IDs and the test level in the Allure report."""
    if not item.config.getoption("--alluredir", default=None):
        return
    import allure

    allure.dynamic.parent_suite(level_of(item))
    for req_id in requirement_labels(item):
        allure.dynamic.tag(req_id)
        allure.dynamic.label("requirement", req_id)
