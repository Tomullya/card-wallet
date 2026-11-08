import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from check_docs import find_requirement_refs, find_test_refs, problems  # noqa: E402


@pytest.mark.req("NFR-08")
def test_finds_requirement_refs():
    assert find_requirement_refs("see BR-PAY-03 and NFR-01, not BR-PAY") == {"BR-PAY-03", "NFR-01"}


@pytest.mark.req("NFR-08")
def test_finds_test_refs_and_strips_params():
    text = "Automated by `tests/api/test_x.py::test_a[1]` and tests/db/test_y.py::test_b."
    assert find_test_refs(text) == {"tests/api/test_x.py::test_a", "tests/db/test_y.py::test_b"}


@pytest.mark.req("NFR-08")
def test_problems_reports_unknown_test_and_requirement(tmp_path):
    (tmp_path / "tc.md").write_text(
        "BR-PAY-03 BR-PAY-99 `tests/api/test_x.py::test_a` `tests/api/test_x.py::test_gone`"
    )
    found = problems(tmp_path, {"BR-PAY-03"}, {"tests/api/test_x.py::test_a"})
    text = "\n".join(found)
    assert "BR-PAY-99" in text and "test_gone" in text and "tc.md" in text
    assert len(found) == 2


@pytest.mark.req("NFR-08")
def test_problems_skips_generated_matrix(tmp_path):
    (tmp_path / "traceability-matrix.md").write_text("BR-NOPE-01")
    assert problems(tmp_path, set(), set()) == []
