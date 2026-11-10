"""Content of the ISTQB trainer site is complete and well-formed (NFR-11)."""

import json
import re
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[2] / "site/istqb"
CONTENT = SITE / "content"

# Learning objectives counted in ISTQB_CTFL_Syllabus_v4.0.1.pdf (and the RSTQB RU v4.0.1 PDF).
LO_COUNT = 64
SECTIONS = [
    "1.1", "1.2", "1.3", "1.4", "1.5",
    "2.1", "2.2", "2.3",
    "3.1", "3.2",
    "4.1", "4.2", "4.3", "4.4", "4.5",
    "5.1", "5.2", "5.3", "5.4", "5.5",
    "6.1", "6.2",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def syllabus():
    return load(CONTENT / "syllabus.json")


def all_los():
    return {lo["id"]: (s["id"], lo) for c in syllabus()["chapters"] for s in c["sections"] for lo in s["los"]}


def questions():
    return load(CONTENT / "questions.json")


def section_files():
    return sorted((CONTENT / "sections").glob("*.json"))


def both(pair) -> bool:
    return isinstance(pair, dict) and all(str(pair.get(lang, "")).strip() for lang in ("ru", "en"))


@pytest.mark.req("NFR-11")
def test_syllabus_shape():
    data = syllabus()
    assert data["version"] == "4.0.1"
    chapters = data["chapters"]
    assert [c["id"] for c in chapters] == ["1", "2", "3", "4", "5", "6"]
    assert [c["minutes"] for c in chapters] == [180, 130, 80, 390, 335, 20]
    assert [s["id"] for c in chapters for s in c["sections"]] == SECTIONS
    for c in chapters:
        assert both(c["title"])
        for s in c["sections"]:
            assert both(s["title"]) and s["id"].startswith(c["id"] + ".")
            for lo in s["los"]:
                assert re.fullmatch(r"FL-\d\.\d\.\d", lo["id"]) and lo["id"][3:6] == s["id"]
                assert lo["k"] in {"K1", "K2", "K3"}
                assert both(lo["quote"])
    assert len(all_los()) == LO_COUNT
    assert len(data["links"]["samples"]) == 4


def _question_ids():
    return [q["id"] for q in questions()] or ["(none)"]


@pytest.mark.req("NFR-11")
@pytest.mark.parametrize("qid", _question_ids())
def test_question_shape(qid):
    if qid == "(none)":
        pytest.skip("question bank is empty")
    q = next(x for x in questions() if x["id"] == qid)
    los = all_los()
    assert q["lo"] in los, "unknown learning objective"
    assert los[q["lo"]][0] == q["section"], "section does not match the objective"
    if q.get("exam", True):  # exam questions have the K-level of their objective
        assert q["k"] == los[q["lo"]][1]["k"]
    else:  # quiz-only warm-up questions may be easier, never harder
        assert q["k"] <= los[q["lo"]][1]["k"]
    assert both(q["q"]) and both(q["why"])
    ru, en = q["options"]["ru"], q["options"]["en"]
    assert len(ru) == len(en) >= 3, "RU and EN must have the same options"
    assert all(str(o).strip() for o in ru + en)
    assert all(0 <= a < len(ru) for a in q["answer"]) and len(set(q["answer"])) == len(q["answer"])
    assert (len(q["answer"]) == 2) == (len(ru) == 5), "select-TWO questions have 5 options"


@pytest.mark.req("NFR-11")
def test_question_ids_unique():
    ids = [q["id"] for q in questions()]
    assert len(ids) == len(set(ids))


@pytest.mark.req("NFR-11")
@pytest.mark.parametrize("path", section_files() or [None], ids=lambda p: p.stem if p else "none")
def test_section_files(path):
    if path is None:
        pytest.skip("no section files yet")
    data = load(path)
    assert data["id"] == path.stem and data["id"] in SECTIONS
    expected = [lo for lo, (sec, _) in all_los().items() if sec == data["id"]]
    assert [o["lo"] for o in data["objectives"]] == expected
    for o in data["objectives"]:
        assert o["explain"]["ru"] and o["explain"]["en"]
        assert all(p.strip() for p in o["explain"]["ru"] + o["explain"]["en"])
        assert both({"ru": o["wallet"]["ru"], "en": o["wallet"]["en"]})
    assert len(data["terms"]) >= 3
    for term in data["terms"]:
        assert term["ru"].strip() and term["en"].strip() and both(term["explain"])


@pytest.mark.req("NFR-11")
def test_every_lo_has_two_questions():
    count = {lo: 0 for lo in all_los()}
    for q in questions():
        if q.get("exam", True):
            count[q["lo"]] += 1
    assert [lo for lo, n in count.items() if n < 2] == []
    assert len(questions()) >= 130
