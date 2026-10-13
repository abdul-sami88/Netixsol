# Production Dockerfile for Render Cloud Deployment
# City Care Clinics Multi-Agent Healthcare Platform

FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files & keep stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    DATABASE_URL=sqlite:///data/city_care_clinics.db \
    PYTHONPATH=/app

# Install minimal OS build dependencies & curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies with web server runtime
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt fastapi uvicorn python-multipart jinja2

# Copy repository (including data/city_care_clinics.db and data/chroma_db)
COPY . .

# Expose default internal port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start Uvicorn bound to Render dynamic $PORT
CMD ["sh", "-c", "uvicorn src.server.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
