#!/bin/bash
# Script to run Next.js frontend

set -e

# Move to the repository root directory
cd "$(dirname "$0")/.."

echo "=== Launching Next.js Frontend on http://localhost:3000 ==="
cd frontend
npm run dev
