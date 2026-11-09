"""The trainer checker tells a caught bug from a broken test (NFR-08)."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from grpc_lab_check import case_kind  # noqa: E402


def case(xml: str):
    return ET.fromstring(xml)


@pytest.mark.req("NFR-08")
def test_assertion_is_a_catch():
    c = case('<testcase name="t"><failure message="assert None == \'hunt-1\'"/></testcase>')
    assert case_kind(c) == "assertion"


@pytest.mark.req("NFR-08")
def test_rpc_error_is_not_a_catch():
    c = case('<testcase name="t"><failure message="grpc.RpcError: unavailable"/></testcase>')
    assert case_kind(c) == "error"


@pytest.mark.req("NFR-08")
def test_passed_case():
    assert case_kind(case('<testcase name="t"/>')) == "passed"
