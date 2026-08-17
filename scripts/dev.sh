#!/usr/bin/env bash
# Self-contained local dev stack: Postgres (compose) + optional import + FastAPI.
# Usage:
#   ./scripts/dev.sh              start DB (if needed), import when empty, run API
#   ./scripts/dev.sh --import     re-import extab before starting API
#   ./scripts/dev.sh --db-only    start Postgres only
#   ./scripts/dev.sh --import-only
#   ./scripts/dev.sh --prod       Gunicorn + Uvicorn workers (no reload; D-54)
#   ./scripts/dev.sh stop         docker compose down (keeps volume)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT}/web/docker-compose.yml"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://raa:raa@localhost:5432/raa_modernized}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"

IMPORT=0
DB_ONLY=0
IMPORT_ONLY=0
PROD=0
ACTION=start

for arg in "$@"; do
  case "$arg" in
    --import) IMPORT=1 ;;
    --db-only) DB_ONLY=1 ;;
    --import-only) IMPORT_ONLY=1 ;;
    --prod) PROD=1 ;;
    stop) ACTION=stop ;;
    -h|--help)
      sed -n '2,11p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

# Prefer compose; fall back when the compose plugin is broken (D-42 / D-53).
compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE_FILE" "$@"
  else
    echo "Neither 'docker compose' nor 'docker-compose' is available." >&2
    exit 1
  fi
}

ensure_compose_db() {
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^raa_pg$'; then
    echo "Using existing container 'raa_pg' on :5432."
    return 0
  fi
  if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q '^raa_pg$'; then
    echo "Starting existing container 'raa_pg'..."
    docker start raa_pg >/dev/null
    return 0
  fi
  if ! compose ps --status running --services 2>/dev/null | grep -qx 'db'; then
    echo "Starting Postgres (docker compose)..."
    compose up -d db
  fi
}

wait_for_postgres() {
  echo "Waiting for Postgres on localhost:5432..."
  for _ in $(seq 1 45); do
    if (echo >/dev/tcp/127.0.0.1/5432) >/dev/null 2>&1; then
      if uv run python - <<'PY' >/dev/null 2>&1
import os
from sqlalchemy import create_engine, text
url = os.environ["DATABASE_URL"]
with create_engine(url).connect() as conn:
    conn.execute(text("SELECT 1"))
PY
      then
        echo "Postgres is ready."
        return 0
      fi
    fi
    sleep 1
  done
  echo "Postgres did not become ready in time." >&2
  exit 1
}

persoon_count() {
  DATABASE_URL="$DATABASE_URL" uv run python - <<'PY'
import os
from sqlalchemy import create_engine, text
url = os.environ["DATABASE_URL"]
engine = create_engine(url)
try:
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raa.persoon")).scalar()
        print(int(count or 0))
except Exception:
    print(0)
PY
}

run_import() {
  echo "Importing extab into Postgres..."
  (cd "$ROOT" && uv run python scripts/import_release.py --skip-validate)
}

sync_deps() {
  (cd "$ROOT" && uv sync)
  if [[ "$PROD" -eq 1 ]]; then
    (cd "$ROOT/web/api" && uv sync --group prod)
  else
    (cd "$ROOT/web/api" && uv sync)
  fi
}

start_api() {
  echo "API: http://${API_HOST}:${API_PORT}/"
  cd "$ROOT/web/api"
  if [[ "$PROD" -eq 1 ]]; then
    echo "Runtime: gunicorn (${GUNICORN_WORKERS} uvicorn workers)"
    exec uv run gunicorn raa_api.main:app \
      -k uvicorn.workers.UvicornWorker \
      -w "$GUNICORN_WORKERS" \
      -b "${API_HOST}:${API_PORT}"
  fi
  exec uv run uvicorn raa_api.main:app --reload --host "$API_HOST" --port "$API_PORT"
}

if [[ "$ACTION" == "stop" ]]; then
  compose down
  exit 0
fi

cd "$ROOT"
sync_deps
ensure_compose_db
wait_for_postgres

if [[ "$IMPORT_ONLY" -eq 1 ]]; then
  run_import
  exit 0
fi

COUNT="$(persoon_count)"
if [[ "$IMPORT" -eq 1 || "$COUNT" -lt 1 ]]; then
  if [[ "$COUNT" -ge 1 && "$IMPORT" -eq 1 ]]; then
    echo "Re-import requested (--import)."
  elif [[ "$COUNT" -lt 1 ]]; then
    echo "Database empty (persoon count=${COUNT}); importing."
  fi
  run_import
else
  echo "Database already loaded (${COUNT} persons); skip import (use --import to refresh)."
fi

if [[ "$DB_ONLY" -eq 1 ]]; then
  echo "Postgres ready. Start API with:"
  echo "  ./scripts/dev.sh           # uvicorn --reload"
  echo "  ./scripts/dev.sh --prod    # gunicorn + uvicorn workers"
  exit 0
fi

start_api
