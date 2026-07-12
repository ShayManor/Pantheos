#!/usr/bin/env bash
# Run the full Playwright E2E suite N times in a row (default 20). Any single
# failure aborts with a non-zero exit — the gate for "not flaky".
set -euo pipefail
N="${1:-20}"
cd "$(dirname "$0")/../pantheos"

for i in $(seq 1 "$N"); do
  echo "======== E2E run $i / $N ========"
  if ! npx playwright test "${@:2}"; then
    echo "!!!! FLAKE/FAILURE on run $i/$N !!!!"
    exit 1
  fi
done
echo "==== all $N E2E runs passed, no flakes ===="
