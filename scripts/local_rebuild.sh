#!/bin/bash

# Local Rebuild Script for Sentilyzer Platform
# This script rebuilds all Docker images when common library changes

set -e

echo "🔧 Starting local rebuild of Sentilyzer services..."

# Stop running containers
echo "📦 Stopping existing containers..."
docker-compose down

# Remove existing images to force rebuild
echo "🧹 Removing existing Docker images..."
docker-compose rm -f
docker image prune -f

# Rebuild all services
echo "🏗️  Building all services..."
docker-compose build --no-cache

echo "✅ Local rebuild completed successfully!"
echo ""
echo "To start the services, run:"
echo "  docker-compose up"
echo ""
echo "To view logs, run:"  
echo "  docker-compose logs -f" 