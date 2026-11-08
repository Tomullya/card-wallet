import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from traceability import check, load_requirements, render_matrix  # noqa: E402


@pytest.mark.req("NFR-08")
def test_load_requirements_parses_ids_and_titles(tmp_path):
    (tmp_path / "BR-x.md").write_text(
        "# Title\n\n## BR-PAY-03 Commission\n\ntext\n\n## Glossary\n"
    )
    (tmp_path / "NFR.md").write_text("## NFR-01 Money precision\n")
    assert load_requirements(tmp_path) == {
        "BR-PAY-03": "Commission",
        "NFR-01": "Money precision",
    }


@pytest.mark.req("NFR-08")
def test_render_marks_uncovered():
    md = render_matrix(
        {"BR-X-01": "One", "BR-X-02": "Two"},
        {"BR-X-01": ["tests/api/test_a.py::test_one"]},
    )
    assert "| BR-X-01 |" in md
    assert "tests/api/test_a.py::test_one" in md
    assert "**NOT COVERED**" in md
    assert "Covered: 1 / 2" in md


@pytest.mark.req("NFR-08")
def test_check_reports_unknown_and_uncovered():
    problems = check(
        {"BR-PAY-03": "Commission", "BR-PAY-04": "Daily limit"},
        {"BR-PAY-03": ["t::a"], "BR-PAY-3": ["t::b"]},
    )
    text = "\n".join(problems)
    assert "BR-PAY-3" in text
    assert "BR-PAY-04" in text
    assert len(problems) == 2


@pytest.mark.req("NFR-08")
def test_check_clean():
    assert check({"BR-A-01": "x"}, {"BR-A-01": ["t::a"]}) == []
