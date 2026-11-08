#!/usr/bin/env bash
# Regenerate Python gRPC code from proto/fraudpb/fraud.proto into both services.
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-.venv/bin/python}"
for target in wallet-api fraud-service; do
  rm -rf "$target/fraudpb"
  mkdir -p "$target/fraudpb"
  "$PYTHON" -m grpc_tools.protoc -I proto \
    --python_out="$target" --grpc_python_out="$target" --pyi_out="$target" \
    proto/fraudpb/fraud.proto
  touch "$target/fraudpb/__init__.py"
done
echo "Generated fraudpb in wallet-api/ and fraud-service/"
