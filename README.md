# Sentilyzer - Financial Sentiment Analysis Platform

[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A scalable, maintainable, and extensible platform that transforms financial text data into actionable strategic insights.

## Project Overview

Sentilyzer is a microservice-based system that collects unstructured data such as financial news and social media texts, performs sentiment analysis using the **FinBERT** model, and presents the results through a secure API.

**For more information, check out the project's comprehensive documentation:**

> ### 📚 [Click here for Detailed Documentation](./docs/README.md)

## Quick Setup and Running

You can quickly set up the entire platform (PostgreSQL, Redis, all services) with Docker Compose:

```bash
# Build services and start in background
docker-compose up --build -d
```

**Access Points:**
- **Dashboard**: `http://localhost:8501`
- **Signals API Docs**: `http://localhost:8080/docs`

Please visit our [main documentation page](./docs/README.md) for development environment setup, architectural details, API usage, and more.

## Core Technologies

- **Python**
- **FastAPI** (for API)
- **Celery & Redis** (for Asynchronous tasks)
- **PostgreSQL & Alembic** (for Database and migrations)
- **Transformers & PyTorch** (for Sentiment analysis)
- **Docker & Docker Compose** (for Containerization)
- **Ruff & Pytest** (for Code quality and testing)
