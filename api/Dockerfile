# syntax=docker/dockerfile:1
# FastAPI backend. Build context is the repo root (the API imports db/ and enums/):
#   docker build -f api/Dockerfile .
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so code changes don't invalidate this layer.
# uv.lock is optional (it's gitignored); when present the build uses its pins.
COPY pyproject.toml .python-version uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

COPY enums ./enums
COPY db ./db
COPY migrations ./migrations
COPY api ./api

RUN useradd --system --uid 10001 app
USER app

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=4)"]

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
