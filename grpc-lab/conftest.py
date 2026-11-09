"""Fixtures for the gRPC trainer (docs/grpc-lab). Independent of tests/.

The service address comes from FRAUD_ADDR (default localhost:50051);
scripts/grpc_lab_check.py --buggy points it at the planted-defect copy on :50052.
"""

import os
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(LAB.parent / "fraud-service"))

FRAUD_ADDR = os.getenv("FRAUD_ADDR", "localhost:50051")


@pytest.fixture(scope="session")
def channel():
    """A plain channel: it sends no metadata, every call adds its own."""
    import grpc

    with grpc.insecure_channel(FRAUD_ADDR) as ch:
        yield ch


@pytest.fixture(scope="session")
def stub(channel):
    from fraudpb.fraud_pb2_grpc import FraudServiceStub

    return FraudServiceStub(channel)
