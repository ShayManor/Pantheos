#!/usr/bin/env bash
# Pull the freshly-built image and redeploy the Pantheos compose stack.
# Runs on the mini PC (self-hosted runner). The stack lives at $PANTHEOS_COMPOSE_DIR
# (default ~/pantheos), separate from the repo checkout.
set -euo pipefail

# Repo checkout dir (where this script lives), captured before we cd away — the
# monitoring overlay + configs are synced from here into the compose dir.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="${PANTHEOS_COMPOSE_DIR:-$HOME/pantheos}"
cd "$COMPOSE_DIR"

# Sync the VictoriaMetrics/Alertmanager overlay + its configs into the compose
# dir so CI is the single source of truth. The hand-tuned main docker-compose.yml
# in $COMPOSE_DIR is left untouched; we only add the overlay alongside it.
COMPOSE_FILES=(-f docker-compose.yml)
if [ -f "$SCRIPT_DIR/docker-compose.monitoring.yml" ]; then
  cp "$SCRIPT_DIR/docker-compose.monitoring.yml" "$COMPOSE_DIR/docker-compose.monitoring.yml"
  mkdir -p "$COMPOSE_DIR/monitoring"
  cp "$SCRIPT_DIR"/monitoring/*.yml "$COMPOSE_DIR/monitoring/"
  COMPOSE_FILES+=(-f docker-compose.monitoring.yml)
  echo "==> Synced monitoring overlay + configs into $COMPOSE_DIR"
fi

# Wire the OpenAI key (passed by the deploy job from a GitHub Actions secret)
# into the stack via a gitignored .env that compose interpolates as
# ${OPENAI_API_KEY}. Only that line is managed, and the value is never echoed.
if [ -n "${OPENAI_API_KEY:-}" ]; then
  umask 077
  { grep -v '^OPENAI_API_KEY=' .env 2>/dev/null || true; printf 'OPENAI_API_KEY=%s\n' "$OPENAI_API_KEY"; } > .env.new
  mv .env.new .env
  echo "==> Updated OPENAI_API_KEY in $COMPOSE_DIR/.env"
fi

echo "==> Pulling new image(s) for the stack in $COMPOSE_DIR"
docker compose "${COMPOSE_FILES[@]}" pull

echo "==> Recreating containers with the new image"
docker compose "${COMPOSE_FILES[@]}" up -d --remove-orphans

echo "==> Pruning dangling images"
docker image prune -f

echo "==> Waiting for the app to answer /api/health"
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "Pantheos is healthy."
    docker compose "${COMPOSE_FILES[@]}" ps
    exit 0
  fi
  sleep 2
done

echo "App did not become healthy in time." >&2
docker compose "${COMPOSE_FILES[@]}" logs --tail 60 app || true
exit 1
