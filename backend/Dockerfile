# Backend Dockerfile - FastAPI + Python 3.11
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add redis to requirements (for rate shopper)
RUN pip install --no-cache-dir redis

# Copy application code
COPY . .

# Expose port (Optional, Railway overrides this)
# EXPOSE 8001

# Default command using gunicorn with uvicorn workers for production stability
CMD gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8001} --timeout 120
