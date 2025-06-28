# Multi-stage build for the Data Ingestor service
FROM python:3.10.17-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH="/app"

WORKDIR /app

# Install uv and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

# ----------------- Builder Stage -----------------
FROM base as builder

COPY pyproject.toml .
COPY services/ /app/services/

# Install dependencies for 'data_ingestor' from local project source
RUN uv pip install --system --no-cache ".[data_ingestor]"

# ----------------- Final Application Stage -----------------
FROM builder as application

WORKDIR /app

# Copy and set up the entrypoint script
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# The command to run the Celery Beat scheduler, passed to the entrypoint
CMD ["celery", "-A", "services.data_ingestor.app.tasks.celery_app", "beat", "--loglevel=info"] 