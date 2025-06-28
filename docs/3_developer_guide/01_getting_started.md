# Getting Started: Development Environment Setup

This guide contains the steps needed to start developing the Sentilyzer project on your local machine.

## Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv): A very fast Python package installer.
  ```bash
  # For macOS and Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Docker and Docker Compose (To run the entire system)
- Pre-commit (For Git hooks):
  ```bash
  pip install pre-commit
  ```

## 1. Local Installation (with uv)

This is the recommended method for local development and running tests.

```bash
# 1. Create and activate virtual environment
uv venv

# For macOS/Linux
source .venv/bin/activate
# For Windows
.venv\Scripts\activate

# 2. Install project dependencies (including all services and development tools)
uv pip install -e ".[dev]"

# 3. Set up pre-commit hooks
pre-commit install
```

## 2. Running Services

### With Docker (Recommended for Production and Staging)
The easiest way to run the entire platform is using Docker Compose. It manages the database, Redis, and all microservices.

```bash
# Build and start all services
docker-compose up --build
```

**Access Points:**
- **Dashboard**: `http://localhost:8501`
- **Signals API Docs**: `http://localhost:8080/docs` (Note: Port 8080 from current `docker-compose.yml` is used instead of port 8888 from `README`.)

### Individually (For Focused Development)
If you want to run just a single service locally (e.g., `signals_api`):

```bash
# Make sure dependencies are installed as in Step 1
# Run FastAPI server with uvicorn
uvicorn services.signals_api.app.main:app --host 0.0.0.0 --port 8000 --reload
```
You'll need running PostgreSQL and Redis instances for this. The simplest way is to run them with Docker:
`docker-compose up -d postgres redis`
