# --- Stage 1: Build Stage ---
FROM python:3.11 as builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
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

# Expose the port
EXPOSE 8080

# The command to start the application.
CMD ["uvicorn", "securemed_chat.main:app", "--host", "0.0.0.0", "--port", "8080"]
