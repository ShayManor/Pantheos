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

if [ -z "${PANTHEOS_SERVICE_TOKEN:-}" ]; then
  echo "!!  WARNING: PANTHEOS_SERVICE_TOKEN is unset. Alertmanager's webhook will be" >&2
  echo "!!  rejected by the auth gate, so alerts will not become tickets." >&2
fi

# Bearer credential Alertmanager presents to the Pantheos auth gate. The file
# must exist or Alertmanager refuses to start, so write it unconditionally.
# It is bind-mounted into a container that does not run as this user, so it has
# to be world-readable: a 0600 file would be unreadable inside the container and
# the webhook would silently lose its Authorization header. Confidentiality here
# comes from the file living outside the git tree on a private host.
mkdir -p "$COMPOSE_DIR/monitoring"
printf '%s' "${PANTHEOS_SERVICE_TOKEN:-}" > "$COMPOSE_DIR/monitoring/service-token"
chmod 644 "$COMPOSE_DIR/monitoring/service-token"
echo "==> Wrote Alertmanager service token to $COMPOSE_DIR/monitoring/service-token"

# The app reads the same token from the compose environment as
# ${PANTHEOS_SERVICE_TOKEN}, so persist it alongside OPENAI_API_KEY. Otherwise a
# manual `docker compose up -d` on the mini PC interpolates it to empty and the
# webhook starts getting 401s. Only that line is managed; the value is never echoed.
if [ -n "${PANTHEOS_SERVICE_TOKEN:-}" ]; then
  umask 077
  { grep -v '^PANTHEOS_SERVICE_TOKEN=' .env 2>/dev/null || true; printf 'PANTHEOS_SERVICE_TOKEN=%s\n' "$PANTHEOS_SERVICE_TOKEN"; } > .env.new
  mv .env.new .env
  echo "==> Updated PANTHEOS_SERVICE_TOKEN in $COMPOSE_DIR/.env"
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
    # /api/health is public, so a green health check says nothing about the gate.
    # Probe a gated route: 401 means auth is live, 200 means the dashboard is open.
    code=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/tickets || echo "000")
    if [ "$code" = "200" ]; then
      echo "!!  WARNING: /api/tickets served 200 without a token. The dashboard is OPEN." >&2
      echo "!!  Set FIREBASE_PROJECT_ID in the compose environment to close it." >&2
    else
      echo "==> Auth gate is live (/api/tickets -> $code)"
    fi
    docker compose "${COMPOSE_FILES[@]}" ps
    exit 0
  fi
  sleep 2
done

echo "App did not become healthy in time." >&2
docker compose "${COMPOSE_FILES[@]}" logs --tail 60 app || true
exit 1
