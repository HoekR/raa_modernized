#!/usr/bin/env bash
# Local full stack: Postgres + API + public UI + redactie (background).
#
#   ./scripts/app.sh start          # or ./scripts/start_app.sh
#   ./scripts/app.sh stop           # or ./scripts/stop_app.sh
#   ./scripts/app.sh restart        # or ./scripts/restart_app.sh
#   ./scripts/app.sh status
#
# Options:
#   --no-admin     skip redactie (port 5174)
#   --db           with stop/restart: also stop Postgres (./scripts/dev.sh stop)
#   --import       with start/restart: force extab re-import before API
#
# Logs/PIDs: .run/  (gitignored). See docs/START.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${ROOT}/.run"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-5173}"
ADMIN_PORT="${ADMIN_PORT:-5174}"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg://raa:raa@localhost:5432/raa_modernized}"

WITH_ADMIN=1
STOP_DB=0
DO_IMPORT=0
ACTION=""

usage() {
  sed -n '2,15p' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    start|stop|restart|status) ACTION="$1" ;;
    --no-admin) WITH_ADMIN=0 ;;
    --db) STOP_DB=1 ;;
    --import) DO_IMPORT=1 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

if [[ -z "$ACTION" ]]; then
  usage >&2
  exit 1
fi

mkdir -p "$RUN_DIR"

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
  else
    (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
  fi
}

kill_tree() {
  local pid="$1"
  local children
  children="$(pgrep -P "$pid" 2>/dev/null || true)"
  for c in $children; do
    kill_tree "$c"
  done
  kill "$pid" 2>/dev/null || true
}

stop_named() {
  local name="$1"
  local pidfile="${RUN_DIR}/${name}.pid"
  if [[ ! -f "$pidfile" ]]; then
    return 0
  fi
  local pid
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    echo "Stopping ${name} (pid ${pid})..."
    kill_tree "$pid"
    # Give children a moment, then force if needed
    sleep 0.4
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$pidfile"
}

start_bg() {
  local name="$1"
  local logfile="${RUN_DIR}/${name}.log"
  local pidfile="${RUN_DIR}/${name}.pid"
  shift
  if [[ -f "$pidfile" ]]; then
    local old
    old="$(cat "$pidfile" 2>/dev/null || true)"
    if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null; then
      echo "${name} already running (pid ${old}); skip."
      return 0
    fi
    rm -f "$pidfile"
  fi
  (
    cd "$ROOT"
    exec "$@"
  ) >"$logfile" 2>&1 &
  echo $! >"$pidfile"
  echo "Started ${name} (pid $(cat "$pidfile")) → ${logfile}"
}

ensure_npm() {
  local dir="$1"
  if [[ ! -d "${dir}/node_modules" ]]; then
    echo "npm install in ${dir}..."
    (cd "$dir" && npm install)
  fi
}

cmd_status() {
  echo "PIDs in ${RUN_DIR}:"
  for name in api ui admin; do
    local pidfile="${RUN_DIR}/${name}.pid"
    if [[ -f "$pidfile" ]]; then
      local pid
      pid="$(cat "$pidfile")"
      if kill -0 "$pid" 2>/dev/null; then
        echo "  ${name}: running (pid ${pid})"
      else
        echo "  ${name}: stale pidfile (${pid})"
      fi
    else
      echo "  ${name}: not started via app.sh"
    fi
  done
  echo "Ports:"
  for pair in "API:${API_PORT}" "UI:${UI_PORT}" "admin:${ADMIN_PORT}"; do
    local label="${pair%%:*}"
    local port="${pair##*:}"
    if port_in_use "$port"; then
      echo "  ${label} :${port} listening"
    else
      echo "  ${label} :${port} free"
    fi
  done
}

cmd_stop() {
  stop_named admin
  stop_named ui
  stop_named api
  if [[ "$STOP_DB" -eq 1 ]]; then
    echo "Stopping Postgres (compose)..."
    "${ROOT}/scripts/dev.sh" stop || true
  else
    echo "Postgres left running (use: ./scripts/stop_app.sh --db)."
  fi
  echo "Stopped."
}

cmd_start() {
  if [[ ! -f "${ROOT}/config.local.toml" ]]; then
    echo "Missing config.local.toml — copy config.local.toml.example first." >&2
    exit 1
  fi

  echo "Ensuring Postgres..."
  if [[ "$DO_IMPORT" -eq 1 ]]; then
    # --db-only path does not import; run import-only then keep API separate
    "${ROOT}/scripts/dev.sh" --db-only
    echo "Re-importing (--import)..."
    "${ROOT}/scripts/dev.sh" --import-only
  else
    "${ROOT}/scripts/dev.sh" --db-only
  fi

  # If DB was empty, --db-only skips import. Match dev.sh behaviour: import when empty.
  COUNT="$(
    DATABASE_URL="$DATABASE_URL" uv run python - <<'PY'
import os
from sqlalchemy import create_engine, text
url = os.environ["DATABASE_URL"]
try:
    with create_engine(url).connect() as conn:
        print(int(conn.execute(text("SELECT COUNT(*) FROM raa.persoon")).scalar() or 0))
except Exception:
    print(0)
PY
  )"
  if [[ "$COUNT" -lt 1 && "$DO_IMPORT" -eq 0 ]]; then
    echo "Database empty; importing..."
    "${ROOT}/scripts/dev.sh" --import-only
  fi

  (cd "$ROOT" && uv sync)
  (cd "$ROOT/web/api" && uv sync)

  if port_in_use "$API_PORT" && [[ ! -f "${RUN_DIR}/api.pid" ]]; then
    echo "Port ${API_PORT} already in use (not our pidfile). Stop that process or use another API_PORT." >&2
    exit 1
  fi
  start_bg api bash -c "cd '${ROOT}/web/api' && exec uv run uvicorn raa_api.main:app --reload --host '${API_HOST}' --port '${API_PORT}'"

  ensure_npm "${ROOT}/web/ui"
  if port_in_use "$UI_PORT" && [[ ! -f "${RUN_DIR}/ui.pid" ]]; then
    echo "Port ${UI_PORT} already in use. Stop that process first." >&2
    exit 1
  fi
  start_bg ui bash -c "cd '${ROOT}/web/ui' && exec npm run dev -- --host 127.0.0.1 --port '${UI_PORT}'"

  if [[ "$WITH_ADMIN" -eq 1 ]]; then
    ensure_npm "${ROOT}/web/admin"
    if port_in_use "$ADMIN_PORT" && [[ ! -f "${RUN_DIR}/admin.pid" ]]; then
      echo "Port ${ADMIN_PORT} already in use. Stop that process first (or pass --no-admin)." >&2
      exit 1
    fi
    start_bg admin bash -c "cd '${ROOT}/web/admin' && exec npm run dev -- --host 127.0.0.1 --port '${ADMIN_PORT}'"
  fi

  echo ""
  echo "URLs:"
  echo "  API      http://${API_HOST}:${API_PORT}/"
  echo "  Public   http://127.0.0.1:${UI_PORT}/"
  if [[ "$WITH_ADMIN" -eq 1 ]]; then
    echo "  Redactie http://127.0.0.1:${ADMIN_PORT}/"
  fi
  echo "Logs: ${RUN_DIR}/*.log"
  echo "Stop: ./scripts/stop_app.sh"
}

cmd_restart() {
  cmd_stop
  # After stop with --db, Postgres is down; start brings it back.
  cmd_start
}

case "$ACTION" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  restart) cmd_restart ;;
  status) cmd_status ;;
esac
