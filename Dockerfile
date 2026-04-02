# --- Stage 1: Build Stage ---
FROM python:3.11 AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Stage 2: Final Production Stage ---
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

COPY ./src/ ./src/

EXPOSE 8080

# --- PERFORMANCE REFACTOR ---
# The optimal number of workers for a 1 vCPU environment (like default Cloud Run)
# is typically 2 * (number of cores) + 1, but for I/O bound tasks like this,
# 2-3 workers is a safe bet to handle concurrent requests without
# excessive context switching.
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "securemed_chat.main:app", "--bind", "0.0.0.0:8080", "--error-logfile", "-"]
