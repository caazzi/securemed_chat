# --- Stage 1: Build Stage ---
FROM python:3.11 AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir --upgrade pip
COPY pyproject.toml .
COPY src/ ./src/
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels .

# --- Stage 2: Final Production Stage ---
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "securemed_chat.main:app", "--bind", "0.0.0.0:8080", "--error-logfile", "-"]
