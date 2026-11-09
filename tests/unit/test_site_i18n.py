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
    assert [lesson["id"] for lesson in load("content/lessons.json")] == [
        f"0{i}" for i in range(9)
    ]
