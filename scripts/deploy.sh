#!/bin/bash
# Crosswire deployment script

set -e

echo "=== Crosswire Deployment ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    # Add Docker installation instructions here
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Services started!"
echo "Dashboard: http://localhost:8080"
echo "Webhook: http://localhost:5679"

# Show logs
echo "Showing logs (Ctrl+C to stop)..."
docker-compose logs -f
