# Backend Dockerfile - FastAPI + Python 3.13
FROM python:3.13-slim

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

# Expose port
EXPOSE 8001

# Default command (uses Railway's $PORT or 8001)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}
