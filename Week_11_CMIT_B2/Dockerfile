# ShopKaro AI Commerce Serving Platform — Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code, data, and dashboard
COPY src/ src/
COPY data/ data/
COPY dashboard/ dashboard/
COPY reports/ reports/
COPY main_day5.py .

# Expose FastAPI serving port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD sh -c "curl -f http://localhost:${PORT:-8000}/health || exit 1"

# Command to run production FastAPI server via uvicorn (reads $PORT dynamically for Render/Cloud)
CMD ["sh", "-c", "uvicorn src.serving.api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]

