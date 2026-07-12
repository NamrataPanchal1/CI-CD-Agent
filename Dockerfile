# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and buffering stdout/stderr —
# important for real-time log visibility in `docker logs` / CloudWatch.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first to maximize Docker layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source.
COPY src/ ./src/

# Run as a non-root user for defense-in-depth.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
