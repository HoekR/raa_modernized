#!/usr/bin/env bash
# Restart local API + UIs. Pass --db to bounce Postgres too; --import to re-import.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/app.sh" restart "$@"
