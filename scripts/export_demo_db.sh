#!/usr/bin/env bash
# Export Postgres for SURF demo (Path C). Run from repo root with db up.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-${ROOT}/raa_demo.dump}"

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

pick_compose_file() {
  if [[ -n "${RAA_COMPOSE_FILE:-}" ]]; then
    echo "$RAA_COMPOSE_FILE"
    return
  fi
  local surf="${ROOT}/web/docker-compose.surf.yml"
  local dev="${ROOT}/web/docker-compose.yml"
  for f in "$surf" "$dev"; do
    if compose_with "$f" ps --status running db 2>/dev/null | grep -q db; then
      echo "$f"
      return
    fi
  done
  # Default: local dev export after ./scripts/dev.sh
  echo "$dev"
}

compose_with() {
  COMPOSE_FILE="$1"
  shift
  compose "$@"
}

COMPOSE_FILE="$(pick_compose_file)"

if ! compose ps --status running db 2>/dev/null | grep -q db; then
  echo "Postgres not running. Start with one of:" >&2
  echo "  ./scripts/dev.sh --db-only" >&2
  echo "  ./scripts/surf_stack.sh up-dev   # db only path" >&2
  exit 1
fi

echo "Using compose file: ${COMPOSE_FILE}"
echo "Exporting to ${OUT} ..."
compose exec -T db pg_dump -U raa -Fc raa_modernized > "$OUT"
echo "Done. Copy to SURF: scp ${OUT} user@surf-host:~/raa_modernized/"
echo "Restore there: ./scripts/restore_demo_db.sh raa_demo.dump"
