#!/usr/bin/env python3
"""Check that the automated tests catch every planted defect (BUGGY_MODE).

Each test must PASS against the normal wallet (port 8000) and FAIL with an
assertion error against the buggy wallet (port 8001). A connection error does
not count as "caught".
"""

import os
import subprocess
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORMAL_URL = os.getenv("WALLET_URL", "http://localhost:8000")
BUGGY_URL = os.getenv("BUGGY_WALLET_URL", "http://localhost:8001")

PLANTED = {
    "BUG-01": "tests/api/test_payments.py::test_min_commission_applied",
    "BUG-02": "tests/api/test_payments.py::test_daily_limit_exact_allowed",
    "BUG-03": "tests/api/test_cvv_attempts.py::test_success_resets_counter",
    "BUG-04": "tests/api/test_cards.py::test_other_users_card_and_account_404",
}


def is_up(base_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/api/v1/health", timeout=5) as r:
            return r.status == 200
    except OSError:
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


def run_test(nodeid: str, base_url: str) -> str:
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
            env={**os.environ, "WALLET_URL": base_url},
            capture_output=True,
        )
        return failure_kind(report.read_text()) if report.exists() else "error"


def main() -> int:
    for name, url in (("wallet", NORMAL_URL), ("wallet-buggy", BUGGY_URL)):
        if not is_up(url):
            print(f"ERROR: {name} is not running at {url}")
            print("Start it with: docker compose --profile buggy up -d")
            return 2

    print(f"{'BUG':<7} {'normal':<7} {'buggy':<16} test")
    all_caught = True
    for bug, nodeid in PLANTED.items():
        normal = run_test(nodeid, NORMAL_URL)
        buggy = run_test(nodeid, BUGGY_URL)
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
