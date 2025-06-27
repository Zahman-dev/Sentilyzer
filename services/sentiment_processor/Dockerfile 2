# Multi-stage build for production-ready Python microservice with ML dependencies
FROM python:3.10.17-slim as base

# Set environment variables for Python and pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_DEFAULT_TIMEOUT=1000 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_RETRIES=5

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Upgrade pip to latest version
RUN pip install --upgrade pip setuptools wheel

# Copy pip configuration for timeout optimization
COPY pip.conf /etc/pip.conf

# Create app directory
WORKDIR /app

# Stage 1: Dependencies
FROM base as dependencies

# Copy and install common dependencies first (for better caching)
COPY services/common/requirements.txt /tmp/common-requirements.txt
COPY services/sentiment_processor/requirements.txt /tmp/service-requirements.txt

# Install common dependencies first with retry and timeout settings
RUN pip install --no-cache-dir \
    --timeout=1000 \
    --retries=5 \
    -r /tmp/common-requirements.txt

# Install ML dependencies with CPU-only PyTorch and timeout settings
# Using PyTorch CPU index to avoid downloading CUDA packages
RUN pip install --no-cache-dir \
    --timeout=1000 \
    --retries=5 \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.1.1+cpu \
    && pip install --no-cache-dir \
    --timeout=1000 \
    --retries=5 \
    transformers==4.36.0 \
    numpy==1.24.3 \
    scikit-learn==1.3.2 \
    asyncpg==0.29.0

# Stage 2: Application
FROM dependencies as application

# Copy common modules with proper structure
COPY services/common/app /app/common
COPY services/common/alembic /app/alembic
COPY services/common/alembic.ini /app/

# Copy service-specific code
COPY services/sentiment_processor/app /app/sentiment_processor

# Create __init__.py files for proper Python package structure
RUN touch /app/__init__.py && \
    touch /app/common/__init__.py && \
    touch /app/sentiment_processor/__init__.py

# Set the working directory to the service
WORKDIR /app/sentiment_processor

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the worker
CMD ["python", "-m", "celery", "worker", "-A", "worker.celery_app", "--loglevel=info"] 