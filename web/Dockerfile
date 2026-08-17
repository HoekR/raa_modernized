# API image for SURF / pilot deploy. Build context: repo root (see .dockerignore).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY . .

RUN uv sync && uv sync --project web/api --group prod

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

WORKDIR /app/web/api
CMD ["uv", "run", "gunicorn", "raa_api.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "-w", "2", "--timeout", "120"]
