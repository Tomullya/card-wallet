"""Every text of the trainer site exists in Russian and English (NFR-09)."""

import json
from pathlib import Path

import pytest

SITE = Path(__file__).resolve().parents[2] / "site/grpc-lab"


def load(name: str):
    return json.loads((SITE / name).read_text(encoding="utf-8"))


def referenced_keys(lessons) -> set[str]:
    keys = set()
    for lesson in lessons:
        keys |= {f"lesson.{lesson['id']}.title", f"lesson.{lesson['id']}.subtitle"}
        for item in lesson.get("quiz", []):
            keys |= {item["q"], item["why"], *item["options"]}
        lid = lesson["id"]
        keys |= {f"l{lid}.theory.{i}" for i in range(1, lesson.get("theory", 0) + 1)}
        keys |= {f"l{lid}.postman.{i}" for i in range(1, lesson.get("postman", 0) + 1)}
        keys |= {f"preset.{p}" for p in lesson.get("presets", [])}
        if lesson.get("example"):
            keys.add(f"l{lid}.example")
        for panel in lesson.get("comic", []):
            keys |= {panel["text"], *([panel["caption"]] if panel.get("caption") else [])}
    return keys


@pytest.mark.req("NFR-09")
def test_same_keys_in_both_languages():
    assert set(load("i18n/ru.json")) == set(load("i18n/en.json"))


@pytest.mark.req("NFR-09")
@pytest.mark.parametrize("lang", ["ru", "en"])
def test_no_empty_texts(lang):
    assert [k for k, v in load(f"i18n/{lang}.json").items() if not str(v).strip()] == []


@pytest.mark.req("NFR-09")
def test_lessons_reference_existing_keys():
    missing = referenced_keys(load("content/lessons.json")) - set(load("i18n/ru.json"))
    assert sorted(missing) == []


@pytest.mark.req("NFR-09")
def test_nine_lessons():
    assert [lesson["id"] for lesson in load("content/lessons.json")] == [f"0{i}" for i in range(9)]


# ---------- ISTQB Lab (NFR-11) ----------

ISTQB = SITE.parent / "istqb"


def istqb_texts(lang: str) -> dict:
    return json.loads((ISTQB / f"i18n/{lang}.json").read_text(encoding="utf-8"))


def istqb_used_keys() -> set[str]:
    """Literal t("...") keys in the code, plus keys built from route and tab names."""
    import re

    keys = set()
    for path in (ISTQB / "js").glob("*.js"):
        keys |= set(re.findall(r'\bt\("([\w.]+)"', path.read_text(encoding="utf-8")))
    keys |= {f"tab.{n}" for n in ("theory", "terms", "quiz", "trainer")}
    keys |= {
        f"page.{p}.{part}"
        for p in ("home", "glossary", "exam")
        for part in ("kicker", "title", "subtitle")
    }
    return keys


@pytest.mark.req("NFR-11")
def test_istqb_same_keys_in_both_languages():
    assert set(istqb_texts("ru")) == set(istqb_texts("en"))


@pytest.mark.req("NFR-11")
@pytest.mark.parametrize("lang", ["ru", "en"])
def test_istqb_no_empty_texts(lang):
    assert [k for k, v in istqb_texts(lang).items() if not str(v).strip()] == []


@pytest.mark.req("NFR-11")
def test_istqb_code_uses_existing_keys():
    assert sorted(istqb_used_keys() - set(istqb_texts("ru"))) == []
