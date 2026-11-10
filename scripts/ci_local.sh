#!/usr/bin/env bash
# Everything CI runs, in the same order. Usage: scripts/ci_local.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
step() { printf '\n=== %s ===\n' "$1"; }

wait_healthy() {  # $1 = base URL
  for _ in $(seq 1 60); do
    if curl -fs "$1/api/v1/health" | grep -q '"status":"ok"'; then return 0; fi
    sleep 1
  done
  echo "Service at $1 did not become healthy" >&2
  docker compose --profile buggy logs --tail 50 >&2 || true
  return 1
}

step "Lint"
"$PY" -m ruff check .

step "Frontend type check and build"
npm --prefix frontend ci --no-audit --no-fund --silent
npm --prefix frontend run build --silent

step "Trainer sites: logic tests (Node)"
node --test "site/grpc-lab/tests/*.test.mjs" "site/istqb/tests/*.test.mjs"

step "Unit tests (no services needed)"
"$PY" -m pytest tests/unit -q

step "Start the stack (normal + buggy wallet)"
docker compose --profile buggy up -d --build
wait_healthy http://localhost:8000
wait_healthy http://localhost:8001
wait_healthy http://localhost:3000  # frontend proxies /api to the wallet

step "All automated tests incl. browser E2E (Allure results)"
rm -rf reports/allure-results
"$PY" -m pytest -q --alluredir reports/allure-results --junitxml reports/pytest.xml

step "gRPC trainer: reference solutions pass, exercises import cleanly"
"$PY" -m pytest -q -p no:cacheprovider grpc-lab/solutions
"$PY" -m pytest -q -p no:cacheprovider --collect-only grpc-lab/exercises > /dev/null

step "Postman collection (Newman)"
scripts/run_newman.sh

step "Traceability: every requirement has a test"
"$PY" scripts/traceability.py

step "QA docs reference only existing requirements and tests"
"$PY" scripts/check_docs.py

step "Planted defects are caught (BUGGY_MODE)"
"$PY" scripts/verify_bugs_caught.py

step "Allure report"
npx --no-install allure generate reports/allure-results -o reports/allure-report --clean

step "gRPC Lab site next to the Allure report (published on GitHub Pages)"
mkdir -p reports/allure-report/grpc-lab
cp -R site/grpc-lab/. reports/allure-report/grpc-lab/
rm -rf reports/allure-report/grpc-lab/tests

step "ISTQB Lab site next to the Allure report (published on GitHub Pages)"
mkdir -p reports/allure-report/istqb
cp -R site/istqb/. reports/allure-report/istqb/
rm -rf reports/allure-report/istqb/tests

printf '\nCI OK\n'
