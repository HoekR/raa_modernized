#!/usr/bin/env bash
# SURF demo stack — Postgres + API + nginx (static UI/admin). Run from repo root.
#
#   ./scripts/surf_stack.sh setup          # copy SURF config examples
#   ./scripts/surf_stack.sh build-ui       # npm build ui + admin (/redactie)
#   ./scripts/surf_stack.sh up             # db + api + nginx on :80
#   ./scripts/surf_stack.sh import         # one-shot extab import (needs data mount)
#   ./scripts/surf_stack.sh up-dev         # db + api only; UIs via npm on host
#   ./scripts/surf_stack.sh down
#   ./scripts/surf_stack.sh status
#   ./scripts/surf_stack.sh logs [service]
#
# Path C (no extab on SURF): export_demo_db.sh locally, scp dump, restore_demo_db.sh, then up.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="${ROOT}/web/docker-compose.surf.yml"
HOST="${SURF_PUBLIC_HOST:-localhost}"

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE" "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f "$COMPOSE" "$@"
  else
    echo "Need docker compose or docker-compose plugin." >&2
    exit 1
  fi
}

need_config() {
  if [[ ! -f "${ROOT}/config.local.toml" ]]; then
    echo "Missing config.local.toml — run: ./scripts/surf_stack.sh setup" >&2
    exit 1
  fi
}

cmd_setup() {
  if [[ ! -f "${ROOT}/config.local.toml" ]]; then
    cp "${ROOT}/config.surf.toml.example" "${ROOT}/config.local.toml"
    echo "Created config.local.toml from config.surf.toml.example — edit YOUR-SURF-HOST and api_key."
  else
    echo "config.local.toml already exists (unchanged)."
  fi
  if [[ ! -f "${ROOT}/data_manifest.local.toml" ]]; then
    cp "${ROOT}/data_manifest.surf.toml.example" "${ROOT}/data_manifest.local.toml"
    echo "Created data_manifest.local.toml — edit /data mount path to extab.pkl."
  else
    echo "data_manifest.local.toml already exists (unchanged)."
  fi
}

cmd_build_ui() {
  echo "Building public UI..."
  (cd "${ROOT}/web/ui" && npm ci && npm run build)
  echo "Building admin UI (base /redactie)..."
  (cd "${ROOT}/web/admin" && npm ci && ADMIN_BASE_PATH=/redactie npm run build)
  echo "Static builds ready: web/ui/build, web/admin/build"
}

cmd_up() {
  need_config
  if [[ ! -d "${ROOT}/web/ui/build" ]] || [[ ! -d "${ROOT}/web/admin/build" ]]; then
    echo "Missing static builds — running build-ui..."
    cmd_build_ui
  fi
  compose --profile full up -d db
  echo "Waiting for Postgres..."
  compose exec -T db pg_isready -U raa -d raa_modernized >/dev/null
  compose --profile full up -d api nginx
  cmd_status
}

cmd_up_dev() {
  need_config
  compose up -d db api
  echo ""
  echo "Dev mode — run on this host (bind 0.0.0.0):"
  echo "  cd web/ui   && npm run dev -- --host 0.0.0.0 --port 5173"
  echo "  cd web/admin && npm run dev -- --host 0.0.0.0 --port 5174"
  echo "Set cors_origins in config.local.toml to http://${HOST}:5173 and :5174"
  cmd_status
}

cmd_import() {
  need_config
  if [[ ! -f "${ROOT}/data_manifest.local.toml" ]]; then
    echo "Missing data_manifest.local.toml" >&2
    exit 1
  fi
  compose up -d db
  compose exec -T db pg_isready -U raa -d raa_modernized >/dev/null
  RAA_DATA_MOUNT="${RAA_DATA_MOUNT:-/data}" DATA_ENV="${DATA_ENV:-researchcloud}" \
    compose --profile import run --rm import
}

cmd_down() {
  compose --profile full down
}

cmd_status() {
  echo ""
  echo "=== RAA SURF stack ==="
  compose ps 2>/dev/null || true
  if curl -sf "http://127.0.0.1:8000/api/health" >/dev/null 2>&1; then
    echo "API health: ok (http://${HOST}:8000/api/health)"
  fi
  if curl -sf "http://127.0.0.1/api/health" >/dev/null 2>&1; then
    echo "Nginx + API: ok"
    echo "  Public UI:  http://${HOST}/"
    echo "  Redactie:   http://${HOST}/redactie/"
  fi
  echo ""
  echo "Docs: docs/SURF_DEMO.md · Demo script: docs/EDITORIAL_DEMO.md"
}

cmd_logs() {
  compose logs -f "${1:-}"
}

chmod_scripts() {
  chmod +x "${ROOT}/scripts/export_demo_db.sh" "${ROOT}/scripts/restore_demo_db.sh" 2>/dev/null || true
}

main() {
  chmod_scripts
  cd "$ROOT"
  case "${1:-}" in
    setup) cmd_setup ;;
    build-ui) cmd_build_ui ;;
    up) cmd_up ;;
    up-dev) cmd_up_dev ;;
    import) cmd_import ;;
    down) cmd_down ;;
    status) cmd_status ;;
    logs) shift; cmd_logs "$@" ;;
    *)
      sed -n '2,14p' "$0"
      exit 1
      ;;
  esac
}

main "$@"
