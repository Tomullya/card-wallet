#!/usr/bin/env python3
"""Check docs/qa: every requirement ID and every automated test a document names must exist."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from traceability import REQ_DIR, load_requirements  # noqa: E402

DOCS = ROOT / "docs" / "qa"
SKIP = {"traceability-matrix.md"}
REQ_REF = re.compile(r"\b(?:BR-[A-Z]+-\d{2}|NFR-\d{2})\b")
TEST_REF = re.compile(r"\b(tests/[\w/]+\.py::\w+)")


def find_requirement_refs(text: str) -> set[str]:
    return set(REQ_REF.findall(text))


def find_test_refs(text: str) -> set[str]:
    return set(TEST_REF.findall(text))


def problems(doc_dir: Path, requirements: set[str], test_nodeids: set[str]) -> list[str]:
    found = []
    for path in sorted(doc_dir.rglob("*.md")):
        if path.name in SKIP:
            continue
        text = path.read_text()
        name = path.relative_to(doc_dir)
        found += [
            f"{name}: unknown requirement {r}"
            for r in sorted(find_requirement_refs(text) - requirements)
        ]
        found += [
            f"{name}: test does not exist {t}" for t in sorted(find_test_refs(text) - test_nodeids)
        ]
    return found


def collect_test_nodeids() -> set[str]:
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return {line.split("[")[0] for line in out.splitlines() if "::" in line}


def main() -> int:
    found = problems(DOCS, set(load_requirements(REQ_DIR)), collect_test_nodeids())
    for p in found:
        print(f"ERROR: {p}")
    print(f"Docs check: {len(found)} problem(s) in {DOCS.relative_to(ROOT)}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
