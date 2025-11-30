#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure Homebrew binaries (like tesseract) are on PATH for "macOS"
export PATH="/opt/homebrew/bin:$PATH"

echo "Starting Celery Worker (foreground)..."

run_celery () {
  "$1" -A src.services.celery:celery_app worker --loglevel=info --pool=threads --without-gossip --without-mingle --without-heartbeat
}

# Try Poetry-managed environment first
if command -v poetry >/dev/null 2>&1; then
  POETRY_ENV_PATH="$(poetry env info -p 2>/dev/null)"
  if [ -n "$POETRY_ENV_PATH" ] && [ -x "$POETRY_ENV_PATH/bin/celery" ]; then
    run_celery "$POETRY_ENV_PATH/bin/celery"
    exit $?
  fi
fi

# Fallback to whichever celery is on PATH
if command -v celery >/dev/null 2>&1; then
  run_celery "$(command -v celery)"
  exit $?
fi

echo "Celery command not found. Activate your virtual environment or install dependencies."
exit 1