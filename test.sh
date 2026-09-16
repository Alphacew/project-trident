#!/usr/bin/env bash
set -e

# Run TRIDENT Phase 1 Verification Suite
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating .venv..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

echo "================================================="
echo "Running TRIDENT Invariant & Integration Tests..."
echo "================================================="
.venv/bin/pytest -v --cov=backend tests/
echo "================================================="
echo "All Invariant & Verification Tests Passed!"
echo "================================================="
