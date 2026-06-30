#!/bin/bash
# Script to run FastAPI backend server

set -e

# Move to the repository root directory
cd "$(dirname "$0")/.."

# Path to virtual env python execution
PYTHON_EXEC="backend/.venv/bin/python"

if [ ! -f "$PYTHON_EXEC" ]; then
    echo "Error: Virtual environment python not found at backend/.venv/bin/python."
    echo "Please execute: bash scripts/setup.sh first."
    exit 1
fi

echo "=== Launching FastAPI Backend on http://localhost:8000 ==="
cd backend
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
