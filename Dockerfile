# --- Stage 1: Build Frontend ---
FROM python:3.11-slim-bookworm AS builder

# Install Node.js for Reflex frontend compilation
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs unzip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
ENV PATH="/uv/bin:$PATH"

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Copy the entire project for build
COPY . .

# Build Reflex frontend
WORKDIR /app/reflex_app
RUN uv run reflex export --frontend-only --no-zip

# --- Stage 2: Final Production Image ---
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install uv for the final runtime too (cleaner for running scripts)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/
ENV PATH="/uv/bin:$PATH"

# Copy the built project and venv from builder
COPY --from=builder /app /app

# Set up environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app/src"

# Expose ports (Reflex default is 8000 for backend, 3000 for frontend, 
# but in prod it's consolidated or served differently)
# We will run reflex in prod mode which binds to 8080 (Cloud Run default)
EXPOSE 8080

WORKDIR /app/reflex_app
# Run reflex in production mode on port 8080
CMD ["uv", "run", "reflex", "run", "--env", "prod", "--backend-port", "8080", "--frontend-port", "8080"]
