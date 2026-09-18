#!/usr/bin/env bash
# Stop local API + UIs started by start_app.sh. Pass --db to also stop Postgres.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/app.sh" stop "$@"
