#!/usr/bin/env bash
# Whole-project test gate: backend (100% coverage) + frontend E2E.
# Pass an iteration count to loop the E2E suite, e.g. `scripts/test-all.sh 20`.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
N="${1:-1}"

echo "==== backend: pytest (100% coverage) ===="
cd "$ROOT/pantheos-api"
source venv/bin/activate
PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH" python -m pytest -q

echo "==== frontend: E2E x$N ===="
bash "$ROOT/scripts/e2e-loop.sh" "$N"
echo "==== all green ===="
