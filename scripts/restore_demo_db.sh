#!/usr/bin/env bash
# Restore Postgres dump on SURF (Path C). Run from repo root with db up.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${RAA_COMPOSE_FILE:-${ROOT}/web/docker-compose.surf.yml}"
DUMP="${1:-${ROOT}/raa_demo.dump}"

if [[ ! -f "$DUMP" ]]; then
  echo "Dump not found: $DUMP" >&2
  exit 1
fi

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_FILE" "$@"
  else
    echo "Need docker compose or docker-compose." >&2
    exit 1
  fi
}

compose up -d db
echo "Waiting for Postgres..."
for _ in $(seq 1 30); do
  if compose exec -T db pg_isready -U raa -d raa_modernized >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Restoring ${DUMP} (this may take a minute)..."
compose exec -T db pg_restore -U raa -d raa_modernized --clean --if-exists --no-owner --no-acl < "$DUMP"
echo "Restore complete. Start stack: ./scripts/surf_stack.sh build-ui && ./scripts/surf_stack.sh up"
