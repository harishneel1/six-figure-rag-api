#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting the API server (Uvicorn)..."

# ! In case you are not using Poetry
# uvicorn src.server:app --reload --host 0.0.0.0 --port 8000

# ! In case you are using Poetry 
poetry run uvicorn src.server:app --reload --host 0.0.0.0 --port 8000