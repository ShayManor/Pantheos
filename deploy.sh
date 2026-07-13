#!/usr/bin/env bash
# Pull the freshly-built image and redeploy the Pantheos compose stack.
# Runs on the mini PC (self-hosted runner). The stack lives at $PANTHEOS_COMPOSE_DIR
# (default ~/pantheos), separate from the repo checkout.
set -euo pipefail

COMPOSE_DIR="${PANTHEOS_COMPOSE_DIR:-$HOME/pantheos}"
cd "$COMPOSE_DIR"

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
docker compose pull

echo "==> Recreating containers with the new image"
docker compose up -d --remove-orphans

echo "==> Pruning dangling images"
docker image prune -f

echo "==> Waiting for the app to answer /api/health"
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8000/api/health >/dev/null 2>&1; then
    echo "Pantheos is healthy."
    docker compose ps
    exit 0
  fi
  sleep 2
done

echo "App did not become healthy in time." >&2
docker compose logs --tail 60 app || true
exit 1
