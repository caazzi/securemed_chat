# --- Stage 1: Build Stage ---
FROM python:3.11 as builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
# Add gunicorn here so it's included in the wheels
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Stage 2: Final Production Stage ---
FROM python:3.11-slim
WORKDIR /app

# Set the PYTHONPATH to the location where the code will be.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Copy dependencies and install them
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Create a non-root user and give it ownership of the app directory.
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Copy the application source code into the final WORKDIR
COPY ./src/ ./src/

# Expose the port that gunicorn will listen on
EXPOSE 8080

# --- FIX: Update Gunicorn command to prevent buffering and improve logging ---
# -w 4: Starts 4 worker processes.
# -k uvicorn.workers.UvicornWorker: Tells gunicorn to use uvicorn's worker class.
# --bind 0.0.0.0:8080: Binds to the port expected by Cloud Run.
# --access-logfile - --error-logfile -: Streams logs directly to stdout/stderr for Cloud Logging.
# --no-sendfile: Can prevent issues with reverse proxies like Google's Frontend.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "securemed_chat.main:app", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-", "--no-sendfile"]
