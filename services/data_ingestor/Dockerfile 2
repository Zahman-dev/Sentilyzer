# Multi-stage build for production-ready Python microservice
FROM python:3.10.17-slim as base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Stage 1: Dependencies
FROM base as dependencies

# Copy and install common dependencies first (for better caching)
COPY services/common/requirements.txt /tmp/common-requirements.txt
COPY services/data_ingestor/requirements.txt /tmp/service-requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /tmp/common-requirements.txt && \
    pip install --no-cache-dir -r /tmp/service-requirements.txt

# Stage 2: Application
FROM dependencies as application

# Copy common modules with proper structure
COPY services/common/app /app/common
COPY services/common/alembic /app/alembic
COPY services/common/alembic.ini /app/

# Copy service-specific code
COPY services/data_ingestor/app /app/data_ingestor

# Create __init__.py files for proper Python package structure
RUN touch /app/__init__.py && \
    touch /app/common/__init__.py && \
    touch /app/data_ingestor/__init__.py

# Set the working directory to the service
WORKDIR /app/data_ingestor

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run the main application
CMD ["python", "-m", "main"] 