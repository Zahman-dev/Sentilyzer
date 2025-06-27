# Multi-stage build for the Sentiment Processor service
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

# STEP 1: Install Torch from its dedicated index first.
# This avoids dependency confusion where uv might look for other packages
# in the PyTorch index, which can cause errors.
RUN uv pip install \
    --system \
    --no-cache \
    "torch==2.1.1" \
    --index-url https://download.pytorch.org/whl/cpu

# STEP 2: Install the rest of the project dependencies from the default index (PyPI).
# uv is smart enough to see that torch is already installed and will not fetch it again.
RUN uv pip install --system --no-cache ".[sentiment_processor]"

# Create a non-root user for security
RUN groupadd -r worker && useradd -r -g worker worker
RUN mkdir -p /home/worker/.cache && chown -R worker:worker /home/worker
ENV TRANSFORMERS_CACHE="/home/worker/.cache"
USER worker

# ----------------- Final Application Stage -----------------
FROM builder as application

WORKDIR /app

CMD ["celery", "-A", "services.sentiment_processor.app.worker.celery_app", "worker", "--loglevel=info"] 