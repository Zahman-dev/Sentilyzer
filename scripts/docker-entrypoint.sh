#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# This script is a placeholder for more complex startup logic.
# A robust version would include waiting for the database to be ready.
# For now, we rely on Docker Compose's `depends_on` with health checks.

echo "Running Alembic migrations..."

# Run migrations using the central alembic.ini
alembic -c services/common/alembic.ini upgrade head

echo "Migrations completed successfully."

# Execute the command passed as arguments to this script (the Dockerfile's CMD)
exec "$@"
