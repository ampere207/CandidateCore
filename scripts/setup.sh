#!/bin/bash
# Setup script for CandidateCore project workspace

set -e

echo "=== Setting up Backend Virtual Environment ==="
if [ ! -d "backend/.venv" ]; then
    python3 -m venv backend/.venv
    echo "Virtual environment created at backend/.venv"
else
    echo "Virtual environment already exists."
fi

echo "=== Installing Backend Dependencies ==="
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
deactivate

echo "=== Installing Frontend Dependencies ==="
cd frontend
npm install
cd ..

echo "=== Workspace Setup Successfully Completed ==="
