#!/usr/bin/env python3
"""Check a gRPC trainer exercise and explain the result in Russian.

Usage:
  .venv/bin/python scripts/grpc_lab_check.py N              your exercise for lesson N
  .venv/bin/python scripts/grpc_lab_check.py N --solutions  the reference solution
  .venv/bin/python scripts/grpc_lab_check.py N --buggy      against the planted-defect copy (:50052)
"""

import argparse
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAB = ROOT / "grpc-lab"
LESSONS = {
    1: "unary",
    2: "metadata",
    3: "status_codes",
    4: "deadlines",
    5: "server_streaming",
    6: "client_streaming",
    7: "bidi",
    9: "bug_hunt",
}


def lesson_file(number: int, solutions: bool) -> Path:
    folder = "solutions" if solutions else "exercises"
    return LAB / folder / f"test_lab_{number:02d}_{LESSONS[number]}.py"


def case_kind(case) -> str:
    """'passed', 'assertion' (the test's own check failed) or 'error' (anything else).

    Same rule as scripts/verify_bugs_caught.py: only a failed assert counts as a caught bug.
    """
    if case.find("error") is not None or case.find("skipped") is not None:
        return "error"
    failure = case.find("failure")
    if failure is None:
        return "passed"
    message = failure.get("message", "")
    return "assertion" if message.startswith(("assert", "AssertionError")) else "error"


def first_line(case) -> str:
    problem = case.find("failure")
    if problem is None:
        problem = case.find("error")
    message = (problem.get("message") or problem.text or "").strip()
    return message.splitlines()[0] if message else "неизвестная ошибка"


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверка задания gRPC-тренажёра")
    parser.add_argument("lesson", type=int, choices=sorted(LESSONS))
    parser.add_argument("--solutions", action="store_true", help="проверить эталонное решение")
    parser.add_argument("--buggy", action="store_true", help="сервис с багами на :50052")
    args = parser.parse_args()

    path = lesson_file(args.lesson, args.solutions)
    env = dict(os.environ)
    if args.buggy:
        env["FRAUD_ADDR"] = "localhost:50052"
    target = env.get("FRAUD_ADDR", "localhost:50051")
    print(f"Урок {args.lesson}: {path.relative_to(ROOT)} → {target}\n")

    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "junit.xml"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(path), "-q", "-p", "no:cacheprovider",
             f"--junitxml={report}"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        if not report.exists():
            print(result.stdout[-2000:] or result.stderr[-2000:])
            return result.returncode or 1
        cases = list(ET.parse(report).getroot().iter("testcase"))

    if args.buggy:
        return buggy_verdict(cases)

    passed = 0
    for case in cases:
        name = case.get("name")
        if case_kind(case) == "passed":
            passed += 1
            print(f"  ✅ {name}")
        else:
            line = first_line(case)
            hint = " ← ещё не написан" if "TODO" in line else ""
            print(f"  ❌ {name}: {line}{hint}")

    print()
    if passed == len(cases):
        print(f"Отлично: все {passed} теста(ов) прошли.")
    elif "connect" in (result.stdout + result.stderr).lower() and passed == 0:
        print("Похоже, сервис не запущен: docker compose --profile buggy up -d")
    else:
        print(f"Прошло {passed} из {len(cases)}. Поправь красные тесты и запусти проверку снова.")
    return result.returncode


def buggy_verdict(cases) -> int:
    """On the planted-defect copy a good test FAILS on its assert: that is a caught bug."""
    caught = 0
    for case in cases:
        name, kind = case.get("name"), case_kind(case)
        if kind == "assertion":
            caught += 1
            print(f"  🐞 {name}: баг пойман — {first_line(case)}")
        elif kind == "passed":
            print(f"  ⚪ {name}: тест прошёл, значит баг НЕ пойман")
        else:
            line = first_line(case)
            hint = " (ещё не написан)" if "TODO" in line else ""
            print(f"  ⚠️ {name}: упал с ошибкой, а не на assert — это не считается{hint}: {line}")
    print()
    if caught == len(cases):
        print(f"Отлично: все {caught} бага пойманы. Проверь, что без --buggy эти тесты зелёные.")
        return 0
    print(f"Поймано {caught} из {len(cases)}. Тест должен падать на assert, а не на ошибке вызова.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
