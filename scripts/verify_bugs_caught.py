#!/usr/bin/env python3
"""Check that the automated tests catch every planted defect (BUGGY_MODE).

Each test must PASS against the normal service and FAIL with an assertion
error against the buggy one: wallet 8000 / 8001, Fraud Service 50051 / 50052.
A connection error does not count as "caught".
"""

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMAL_URL = os.getenv("WALLET_URL", "http://localhost:8000")
BUGGY_URL = os.getenv("BUGGY_WALLET_URL", "http://localhost:8001")
NORMAL_FRAUD = os.getenv("FRAUD_ADDR", "localhost:50051")
BUGGY_FRAUD = os.getenv("BUGGY_FRAUD_ADDR", "localhost:50052")

# bug -> (test node id, which service the test talks to)
PLANTED = {
    "BUG-01": ("tests/api/test_payments.py::test_min_commission_applied", "wallet"),
    "BUG-02": ("tests/api/test_payments.py::test_daily_limit_exact_allowed", "wallet"),
    "BUG-03": ("tests/api/test_cvv_attempts.py::test_success_resets_counter", "wallet"),
    "BUG-04": ("tests/api/test_cards.py::test_other_users_card_and_account_404", "wallet"),
    "BUG-17": ("tests/grpc/test_metadata.py::test_unknown_key_unauthenticated", "fraud"),
    "BUG-18": ("tests/grpc/test_bidi_streaming.py::test_stream_ends_after_client_closes", "fraud"),
    "BUG-19": ("tests/grpc/test_metadata.py::test_request_id_echoed_in_trailers", "fraud"),
}
ENV_VAR = {"wallet": "WALLET_URL", "fraud": "FRAUD_ADDR"}
TARGETS = {"wallet": (NORMAL_URL, BUGGY_URL), "fraud": (NORMAL_FRAUD, BUGGY_FRAUD)}


def is_up(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/api/v1/health", timeout=5) as r:
            return r.status == 200
    except OSError:
        return False


def fraud_is_up(address: str, wait_seconds: float = 30) -> bool:
    import grpc
    from grpc_health.v1 import health_pb2, health_pb2_grpc

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        with grpc.insecure_channel(address) as channel:
            try:
                r = health_pb2_grpc.HealthStub(channel).Check(
                    health_pb2.HealthCheckRequest(service=""), timeout=2
                )
                if r.status == health_pb2.HealthCheckResponse.SERVING:
                    return True
            except grpc.RpcError:
                pass
        time.sleep(1)
    return False


def failure_kind(junit_xml: str) -> str:
    """'passed', 'assertion' (the test's own check failed) or 'error' (anything else).

    Uses the failure *message* from the JUnit report, not the traceback text: a
    traceback shows the test's source lines, which contain the word "assert" even
    when the real cause is a connection error.
    """
    root = ET.fromstring(junit_xml)
    for case in root.iter("testcase"):
        if case.find("error") is not None or case.find("skipped") is not None:
            return "error"
        failure = case.find("failure")
        if failure is not None:
            message = failure.get("message", "")
            is_assert = message.startswith("assert") or message.startswith("AssertionError")
            return "assertion" if is_assert else "error"
    return "passed"


def run_test(nodeid: str, target: str, address: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "junit.xml"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                nodeid,
                "-q",
                "-p",
                "no:cacheprovider",
                f"--junitxml={report}",
            ],
            cwd=ROOT,
            env={**os.environ, ENV_VAR[target]: address},
            capture_output=True,
        )
        return failure_kind(report.read_text()) if report.exists() else "error"


def main() -> int:
    checks = (
        ("wallet", NORMAL_URL, is_up),
        ("wallet-buggy", BUGGY_URL, is_up),
        ("fraud", NORMAL_FRAUD, fraud_is_up),
        ("fraud-buggy", BUGGY_FRAUD, fraud_is_up),
    )
    for name, address, up in checks:
        if not up(address):
            print(f"ERROR: {name} is not running at {address}")
            print("Start it with: docker compose --profile buggy up -d")
            return 2

    print(f"{'BUG':<7} {'normal':<7} {'buggy':<16} test")
    all_caught = True
    for bug, (nodeid, target) in PLANTED.items():
        normal_address, buggy_address = TARGETS[target]
        normal = run_test(nodeid, target, normal_address)
        buggy = run_test(nodeid, target, buggy_address)
        caught = normal == "passed" and buggy == "assertion"
        all_caught &= caught
        buggy_state = {
            "passed": "pass (MISSED)",
            "assertion": "fail (caught)",
            "error": "error (not a catch)",
        }[buggy]
        print(f"{bug:<7} {'pass' if normal == 'passed' else 'FAIL':<7} {buggy_state:<16} {nodeid}")

    print("All planted defects are caught." if all_caught else "Some defects were NOT caught.")
    return 0 if all_caught else 1


if __name__ == "__main__":
    sys.exit(main())
