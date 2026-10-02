# ==============================================================================
# Dockerfile — Production Container for Pakistan Real Estate AI & Serving Engine
# Multi-stage optimized build for FastAPI model serving and MLOps lifecycle
# ==============================================================================

FROM python:3.12-slim AS base

# Avoid buffering stdout/stderr and bytecode generation
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Install Linux system dependencies (libgomp1 for OpenMP acceleration in LightGBM/CatBoost, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specifications first to leverage Docker layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Copy application source code, models, and data
COPY src/ /app/src/
COPY saved_models/ /app/saved_models/
COPY data_cleaned/ /app/data_cleaned/
COPY reports/ /app/reports/
COPY serving_api.py /app/serving_api.py
COPY dashboard.py /app/dashboard.py
COPY drift_monitoring.py /app/drift_monitoring.py
COPY retraining_pipeline.py /app/retraining_pipeline.py
COPY database.py /app/database.py
COPY .env.example /app/.env.example

# Create directories for logs and archive snapshots
RUN mkdir -p /app/saved_models/archive /app/saved_models/rollback /app/reports

# Create non-root user for enterprise container security
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose FastAPI serving port (8000) and Streamlit dashboard port (8501)
EXPOSE 8000 8501

# Container Healthcheck verifying model serving status
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default execution: run FastAPI backend
CMD ["uvicorn", "serving_api:app", "--host", "0.0.0.0", "--port", "8000"]
