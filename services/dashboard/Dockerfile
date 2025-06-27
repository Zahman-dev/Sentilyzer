# Multi-stage build for the Dashboard service
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
COPY services/ /app/services/

# Install dependencies for 'dashboard' from local project source
RUN uv pip install --system --no-cache ".[dashboard]"

# ----------------- Final Application Stage -----------------
FROM builder as application

WORKDIR /app/services/dashboard/app

EXPOSE 8501

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

CMD ["streamlit", "run", "main.py"] 