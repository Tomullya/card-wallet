import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from verify_bugs_caught import failure_kind  # noqa: E402

ASSERTION = """<testsuites><testsuite><testcase name="t">
<failure message="assert '0.10' == '0.50'">E AssertionError: assert '0.10' == '0.50'</failure>
</testcase></testsuite></testsuites>"""

CONNECT = """<testsuites><testsuite><testcase name="t">
<failure message="httpx.ConnectError: [Errno 61] Connection refused">
    assert pay(api, client, card, "60.00").json()["status"] == "APPROVED"
E   httpx.ConnectError: [Errno 61] Connection refused</failure>
</testcase></testsuite></testsuites>"""

PASSED = """<testsuites><testsuite><testcase name="t"/></testsuite></testsuites>"""


@pytest.mark.req("NFR-08")
def test_assertion_failure_counts_as_caught():
    assert failure_kind(ASSERTION) == "assertion"


@pytest.mark.req("NFR-08")
def test_connection_error_is_not_caught_even_with_assert_in_source():
    """Found in final review: the word 'assert' in the traceback source line was enough."""
    assert failure_kind(CONNECT) == "error"


@pytest.mark.req("NFR-08")
def test_passed():
    assert failure_kind(PASSED) == "passed"


@pytest.mark.req("NFR-08")
def test_every_planted_bug_names_its_target():
    from verify_bugs_caught import PLANTED

    assert {target for _, target in PLANTED.values()} == {"wallet", "fraud"}
    assert PLANTED["BUG-17"] == (
        "tests/grpc/test_metadata.py::test_unknown_key_unauthenticated", "fraud"
    )
    assert PLANTED["BUG-18"][0].endswith("test_stream_ends_after_client_closes")
    assert PLANTED["BUG-19"][0].endswith("test_request_id_echoed_in_trailers")
