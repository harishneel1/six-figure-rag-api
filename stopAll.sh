#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Stopping Celery Worker..."
pkill -f "celery.*worker" || echo "No Celery worker process found"

echo "Stopping Redis Server..."
(cd redis && docker-compose -f docker-compose.yaml down)

echo "Stopping the server..."
pkill -f "uvicorn src.server:app" || echo "No uvicorn process found"
echo "Server stopped"