# Multi-stage build for a shared library-like service
FROM python:3.10.17-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH="/app"

WORKDIR /app

# Install uv
RUN pip install uv

# ----------------- Builder Stage -----------------
FROM base as builder

COPY pyproject.toml .
# Copy all service code needed for local installation
COPY services/ /app/services/

# Install only the 'common' dependencies from the local project source
RUN uv pip install --system --no-cache ".[common]"

# ----------------- Final Application Stage -----------------
FROM builder as application

# This image doesn't run on its own.
CMD ["/bin/true"] 