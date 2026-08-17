# Local / CI smoke checks for the RAA pilot.
#   make check      unit tests (no DB)
#   make check-db   unit tests + RQ/X assert (needs Postgres + import)
#   make smoke      RQ baselines + X1–X5 only

.PHONY: check check-db smoke test-api test-root help

help:
	@echo "Targets:"
	@echo "  make check      pytest (root + web/api) — no Postgres"
	@echo "  make check-db   check + validation_rq_smoke --assert"
	@echo "  make smoke      RQ baselines + X1–X5 (Postgres required)"

test-root:
	UV_NO_SYNC=1 uv run --no-sync pytest tests/ -q

test-api:
	cd web/api && UV_NO_SYNC=1 uv run --no-sync pytest -q

check: test-root test-api
	@echo "OK: unit tests passed"

smoke:
	UV_NO_SYNC=1 uv run --no-sync python scripts/validation_rq_smoke.py --assert

check-db: check smoke
	@echo "OK: check-db passed"
