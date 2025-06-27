# Multi-stage build for the Signals API service
FROM python:3.10.17-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH="/app"

WORKDIR /app

# Install uv and system dependencies required for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && pip install uv \
    && rm -rf /var/lib/apt/lists/*

# ----------------- Builder Stage -----------------
FROM base as builder

COPY pyproject.toml .
COPY services/ /app/services/

# Install dependencies for 'signals_api' from local project source
RUN uv pip install --system --no-cache ".[signals_api]"

# ----------------- Final Application Stage -----------------
FROM builder as application

WORKDIR /app

EXPOSE 8000 