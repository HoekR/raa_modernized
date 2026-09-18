#!/usr/bin/env bash
# Start local API + UIs (background). See docs/START.md.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/app.sh" start "$@"
