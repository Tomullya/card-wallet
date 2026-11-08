#!/usr/bin/env bash
# Run the Postman collection with Newman against the local stack.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d node_modules/newman ] || npm ci --silent --no-audit --no-fund
mkdir -p reports
npm run --silent newman
