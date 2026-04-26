# --- Stage 1: Build Stage ---
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Layer caching: Install dependencies first
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy source and README (required by pyproject.toml metadata)
COPY README.md ./
COPY src/ ./src/

# Install the project
RUN uv sync --frozen --no-dev

# --- Stage 2: Final Production Stage ---
FROM python:3.11-slim-bookworm
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy only the environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Update Path to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

COPY src/ ./src/

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "securemed_chat.main:app", "--bind", "0.0.0.0:8080"]
