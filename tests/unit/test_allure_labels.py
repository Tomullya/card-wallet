from types import SimpleNamespace

import pytest

from tests.conftest import level_of, requirement_labels


class FakeItem:
    def __init__(self, marker_args, nodeid="tests/api/test_x.py::test_a"):
        self._markers = [SimpleNamespace(args=a) for a in marker_args]
        self.nodeid = nodeid

    def iter_markers(self, name):
        assert name == "req"
        return iter(self._markers)


@pytest.mark.req("NFR-08")
def test_requirement_labels_reads_req_marker():
    assert requirement_labels(FakeItem([("BR-PAY-03", "NFR-01")])) == ["BR-PAY-03", "NFR-01"]


@pytest.mark.req("NFR-08")
def test_requirement_labels_without_marker():
    assert requirement_labels(FakeItem([])) == []


@pytest.mark.req("NFR-08")
def test_level_from_folder():
    assert level_of(FakeItem([], "tests/integration/test_f.py::test_b")) == "integration"
